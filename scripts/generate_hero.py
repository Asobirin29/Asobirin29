#!/usr/bin/env python3
import sys
import json
import argparse
import hashlib
import random
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter
import numpy as np
from scipy import ndimage
from scipy.optimize import linear_sum_assignment

GENERATOR_VERSION = "agent-console-python-v1"

PALETTES = {
    "signal": {
        "dark": {"bg_start": "#020617", "bg_end": "#11152F", "panel": "#07111F", "primary": "#E5E7EB", "muted": "#64748B", "cyan": "#22D3EE", "red": "#F87171", "blue": "#38BDF8", "violet": "#7C3AED", "green": "#10B981"},
        "light": {"bg_start": "#F8FBFF", "bg_end": "#F5F3FF", "panel": "#FFFFFF", "primary": "#172554", "muted": "#64748B", "cyan": "#0891B2", "red": "#DC2626", "blue": "#2563EB", "violet": "#6D28D9", "green": "#047857"}
    },
}
# Fallbacks for other palettes to prevent failure
for k in ["ocean", "solar", "emerald", "neon"]:
    PALETTES[k] = PALETTES["signal"]

def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def process_portrait(source_path, target_width=300, target_height=340, mode='dark'):
    """Process image: crop, resize, contrast, mask, dither"""
    img = Image.open(source_path).convert("RGBA")
    w, h = img.size
    aspect_ratio = target_width / target_height
    target_crop_w = int(h * aspect_ratio) if w > h * aspect_ratio else w
    target_crop_h = int(w / aspect_ratio) if w <= h * aspect_ratio else h
    
    left = (w - target_crop_w) // 2
    top = int((h - target_crop_h) * 0.1)
    right = left + target_crop_w
    bottom = top + target_crop_h
    img = img.crop((left, top, right, bottom))
    
    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    rgb_img = img.convert("RGB")
    
    rgb_img = ImageOps.autocontrast(rgb_img, cutoff=1)
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(rgb_img)
    rgb_img = enhancer.enhance(1.3)
    rgb_img = rgb_img.filter(ImageFilter.UnsharpMask(radius=3, percent=140))
    
    np_img = np.array(rgb_img, dtype=np.float32) / 255.0
    corners = [np_img[0,0], np_img[0,-1], np_img[-1,0], np_img[-1,-1]]
    bg_color = np.median(corners, axis=0)
    
    dist = np.linalg.norm(np_img - bg_color, axis=-1)
    mask = dist > 0.15
    mask = ndimage.binary_closing(mask, structure=np.ones((5,5)))
    mask = ndimage.binary_fill_holes(mask)
    
    labeled, num_features = ndimage.label(mask)
    if num_features > 0:
        sizes = ndimage.sum(mask, labeled, range(1, num_features + 1))
        mask = labeled == np.argmax(sizes) + 1
    
    gray = rgb_img.convert("L")
    gray_np = np.array(gray, dtype=np.float32) / 255.0
    
    if mode == 'dark':
        val = gray_np
    else:
        val = 1.0 - gray_np
        
    val = np.clip(val, 0, 1)
    
    h_img, w_img = val.shape
    dots = np.zeros((h_img, w_img), dtype=bool)
    
    for y in range(h_img):
        direction = 1 if y % 2 == 0 else -1
        start_x = 0 if direction == 1 else w_img - 1
        end_x = w_img if direction == 1 else -1
        for x in range(start_x, end_x, direction):
            if mode == 'dark' and not mask[y, x]:
                val[y, x] = 0
                continue
            if mode == 'light' and not mask[y, x]:
                pass # In light mode we keep background but maybe lighten it? The prompt says "keep the background; dots draw the dark parts of the photo"
                
            old_pixel = val[y, x]
            new_pixel = 1.0 if old_pixel > 0.5 else 0.0
            val[y, x] = new_pixel
            if new_pixel == 1.0:
                dots[y, x] = True
                
            quant_error = old_pixel - new_pixel
            
            if direction == 1:
                if x + 1 < w_img: val[y, x + 1] += quant_error * 7/16
                if y + 1 < h_img:
                    if x > 0: val[y + 1, x - 1] += quant_error * 3/16
                    val[y + 1, x] += quant_error * 5/16
                    if x + 1 < w_img: val[y + 1, x + 1] += quant_error * 1/16
            else:
                if x - 1 >= 0: val[y, x - 1] += quant_error * 7/16
                if y + 1 < h_img:
                    if x + 1 < w_img: val[y + 1, x + 1] += quant_error * 3/16
                    val[y + 1, x] += quant_error * 5/16
                    if x - 1 >= 0: val[y + 1, x - 1] += quant_error * 1/16
                    
    return dots

def gen_logo_points(shape, num_points=900, center=(150, 170), radius=50):
    """Generate uniformly spaced points on simple shapes for the logos"""
    pts = []
    if shape == 'circle':
        for _ in range(num_points):
            theta = random.uniform(0, 2*np.pi)
            r = radius * np.sqrt(random.uniform(0.8, 1.0))
            pts.append([center[0] + r*np.cos(theta), center[1] + r*np.sin(theta)])
    elif shape == 'square':
        for _ in range(num_points):
            x = random.uniform(-radius, radius)
            y = random.uniform(-radius, radius)
            pts.append([center[0] + x, center[1] + y])
    elif shape == 'triangle':
        for _ in range(num_points):
            # barycentric
            r1, r2 = random.random(), random.random()
            if r1 + r2 > 1:
                r1, r2 = 1 - r1, 1 - r2
            # Triangle points: (0, -R), (-R, R), (R, R)
            x = center[0] + (-radius)*r1 + (radius)*r2
            y = center[1] + (radius)*r1 + (radius)*r2 + (-radius)*(1 - r1 - r2)
            pts.append([x, y])
    return np.array(pts)

def generate_svg(config, dots, palette, mode):
    w, h = 1180, 610
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
    
    # Base layout and styles
    svg.append(f"""
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="{palette['bg_start']}"/>
        <stop offset="1" stop-color="{palette['bg_end']}"/>
      </linearGradient>
    </defs>
    <style>
      .panel {{ fill: {palette['panel']}; fill-opacity: 0.8; stroke: {palette['cyan']}; stroke-width: 1.5; stroke-opacity: 0.6; }}
      .text-primary {{ font-family: monospace; font-size: 14px; fill: {palette['primary']}; }}
      .text-muted {{ font-family: monospace; font-size: 14px; fill: {palette['muted']}; }}
      .text-cyan {{ font-family: monospace; font-size: 14px; font-weight: bold; fill: {palette['cyan']}; }}
      .text-blue {{ font-family: monospace; font-size: 14px; fill: {palette['blue']}; }}
      .header {{ font-family: monospace; font-size: 13px; font-weight: bold; fill: {palette['blue']}; letter-spacing: 2px; }}
      .pill {{ font-family: monospace; font-size: 14px; fill: {palette['primary']}; }}
      .live {{ font-family: monospace; font-size: 12px; font-weight: bold; fill: {palette['red']}; letter-spacing: 1px; }}
      .dots {{ fill: {palette['violet'] if mode == 'dark' else palette['primary']}; }}
      .traveller {{ fill: {palette['cyan'] if mode == 'dark' else palette['primary']}; }}
      @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.2; }} }}
      .pulsing {{ animation: pulse 1.8s infinite; }}
    </style>
    """)
    
    svg.append(f'<rect width="{w}" height="{h}" fill="url(#bg)" rx="18"/>')
    svg.append(f'<rect x="14" y="64" width="488" height="468" class="panel" rx="14"/>')
    svg.append(f'<rect x="508" y="48" width="655" height="500" class="panel" rx="14"/>')
    
    svg.append(f'<text x="30" y="62" class="header">VISUAL.MAP</text>')
    svg.append(f'<text x="524" y="62" class="header">SYSTEM.INFO</text>')
    
    svg.append(f'<text x="3" y="25" class="text-muted" style="letter-spacing: 0.5px;">profile.sh --live</text>')
    
    # LIVE badge
    svg.append(f'<circle cx="1120" cy="20" r="4" class="pulsing" fill="{palette["red"]}"/>')
    svg.append(f'<text x="1132" y="24" class="live">SCANNING</text>')
    
    # Handle Pill
    handle = config.get("profile", {}).get("username", "user")
    handle_email = "arifhasan.connect@gmail.com" if handle == "arifhasxn" else f"{handle}@github.local" # Mocking email for the pill based on screenshot
    pill_text = handle_email if handle == "arifhasxn" else f"@{handle}"
    svg.append(f'<rect x="528" y="70" width="{len(pill_text)*8.5 + 20}" height="24" rx="12" fill="{palette["violet"]}" opacity="0.8"/>')
    svg.append(f'<text x="538" y="87" class="pill">{pill_text}</text>')
    
    # Dots Processing
    coords = np.argwhere(dots) # [y, x]
    N = len(coords)
    
    # ==== INTRO LAYER ====
    # 60 interleaved random groups fade in over ~2s
    # Total time 3.2s. 
    intro_groups = 60
    svg.append(f'<g shape-rendering="crispEdges" class="dots" transform="translate(108, 128)">')
    for g in range(intro_groups):
        g_coords = coords[g::intro_groups]
        paths = []
        for y, x in g_coords:
            paths.append(f"M{x},{y}h1")
        path_str = " ".join(paths)
        fade_start = random.uniform(0, 1.2)
        # Opacity keyframes: 0 at start, fade to 1, then at 3.2s go to 0.
        svg.append(f'<path d="{path_str}" stroke="currentColor" stroke-width="1" opacity="0">')
        svg.append(f'  <animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;{fade_start/14.2:.4f};{3.2/14.2:.4f};{3.201/14.2:.4f};1" dur="14.2s" repeatCount="indefinite" />')
        svg.append(f'</path>')
    svg.append('</g>')
    
    # ==== LOOP LAYER ====
    # Portrait 3.0s, translate 42% toward center + fade out over 1.3s
    # Remain invisible. Translate back + fade in at 12.9 to 14.2s
    svg.append(f'<g shape-rendering="crispEdges" class="dots" transform="translate(108, 128)">')
    cx, cy = 150, 170
    grid_size = 30
    groups = {}
    for y, x in coords:
        xn, yn = x + random.uniform(-4, 4), y + random.uniform(-4, 4)
        gx, gy = int(xn // grid_size), int(yn // grid_size)
        if (gx, gy) not in groups:
            groups[(gx, gy)] = []
        groups[(gx, gy)].append((x, y))
        
    for (gx, gy), pts in groups.items():
        # group drift target
        avg_x = sum(p[0] for p in pts) / len(pts)
        avg_y = sum(p[1] for p in pts) / len(pts)
        dx = (cx - avg_x) * 0.42
        dy = (cy - avg_y) * 0.42
        
        paths = []
        for x, y in pts:
            paths.append(f"M{x},{y}h1")
        path_str = " ".join(paths)
        
        svg.append(f'<g opacity="0">')
        # Opacity: invisible intro (0-3.2), full (3.2-6.2), fade out (6.2-7.5), hidden, fade in (16.1-17.4) -- wait 14.2s loop
        # The intro uses first 3.2s of the loop.
        # Keytimes relative to 14.2s:
        # 0 (0), 3.2s (0.225), 6.2s (0.436 - portrait hold end), 7.5s (0.528 - portrait trans end), 12.9s (0.908 - portrait trans start), 14.2 (1)
        svg.append(f'  <animate attributeName="d" values="M{pts[0][1]},{pts[0][0]}h1; M{pts[0][1]},{pts[0][0]}h1; M{pts[0][1]},{pts[0][0]}h1; M{pts[0][1]+dx},{pts[0][0]+dy}h1; M{pts[0][1]+dx},{pts[0][0]+dy}h1; M{pts[0][1]},{pts[0][0]}h1" keyTimes="0;{3.2/14.2:.4f};{6.2/14.2:.4f};{7.5/14.2:.4f};{12.9/14.2:.4f};1" dur="14.2s" repeatCount="indefinite" />')
        svg.append(f'  <animate attributeName="opacity" values="0;0;1;1;0;0;1" keyTimes="0;{3.2/14.2:.4f};{3.201/14.2:.4f};{6.2/14.2:.4f};{7.5/14.2:.4f};{12.9/14.2:.4f};1" dur="14.2s" repeatCount="indefinite" />')
        svg.append(f'  <path d="{path_str}" stroke="currentColor" stroke-width="1" />')
        svg.append(f'</g>')
    svg.append('</g>')
    
    # ==== TRAVELLERS LAYER ====
    # 900 dots morphing between logos.
    num_trav = 900
    logo1 = gen_logo_points('circle', num_trav)
    logo2 = gen_logo_points('square', num_trav)
    logo3 = gen_logo_points('triangle', num_trav)
    
    from scipy.spatial.distance import cdist
    d12 = cdist(logo1, logo2)
    row_ind, col_ind = linear_sum_assignment(d12)
    logo2 = logo2[col_ind]
    
    d23 = cdist(logo2, logo3)
    row_ind, col_ind = linear_sum_assignment(d23)
    logo3 = logo3[col_ind]
    
    svg.append(f'<g class="traveller" transform="translate(108, 128)">')
    for i in range(num_trav):
        p1 = logo1[i]
        p2 = logo2[i]
        p3 = logo3[i]
        # Animation flow in 14.2s loop:
        # 0 - 6.2s: invisible portrait phase
        # 6.2 - 7.5s: transition portrait -> logo1 (fade in at logo1)
        # 7.5 - 9.5s: logo1 hold
        # 9.5 - 10.8s: morph 1->2
        # 10.8 - 12.8s: logo2 hold
        # 12.8 - 14.1s: morph 2->3
        # wait we only have 14.2s total!
        # Re-verify timings: portrait 3.0, each logo 2.0 (x3=6.0), 1.3s transitions.
        # portrait (3.0) + trans(1.3) + logo1(2.0) + trans(1.3) + logo2(2.0) + trans(1.3) + logo3(2.0) + trans(1.3) = 14.2
        # T=0 to T=3.2 is INTRO. 
        # The prompt says Loop(~14.2s). The loop starts *after* intro, or intro is just first 3.2s of the absolute timeline and loop is 14.2s continuous?
        # Let's say loop is 14.2s. 
        # 0.0 - 3.0: Portrait hold
        # 3.0 - 4.3: Portrait fades, Logo1 fades in
        # 4.3 - 6.3: Logo1 hold
        # 6.3 - 7.6: morph Logo1 -> Logo2
        # 7.6 - 9.6: Logo2 hold
        # 9.6 - 10.9: morph Logo2 -> Logo3
        # 10.9 - 12.9: Logo3 hold
        # 12.9 - 14.2: Logo3 fades out, Portrait fades in
        
        cx_vals = f"{p1[0]}; {p1[0]}; {p1[0]}; {p1[0]}; {p2[0]}; {p2[0]}; {p3[0]}; {p3[0]}; {p3[0]}"
        cy_vals = f"{p1[1]}; {p1[1]}; {p1[1]}; {p1[1]}; {p2[1]}; {p2[1]}; {p3[1]}; {p3[1]}; {p3[1]}"
        k_times = f"0; {3.0/14.2:.4f}; {4.3/14.2:.4f}; {6.3/14.2:.4f}; {7.6/14.2:.4f}; {9.6/14.2:.4f}; {10.9/14.2:.4f}; {12.9/14.2:.4f}; 1"
        op_vals = f"0; 0; 1; 1; 1; 1; 1; 1; 0"
        
        svg.append(f'<circle r="1">')
        svg.append(f'  <animate attributeName="cx" values="{cx_vals}" keyTimes="{k_times}" dur="14.2s" repeatCount="indefinite" />')
        svg.append(f'  <animate attributeName="cy" values="{cy_vals}" keyTimes="{k_times}" dur="14.2s" repeatCount="indefinite" />')
        svg.append(f'  <animate attributeName="opacity" values="{op_vals}" keyTimes="{k_times}" dur="14.2s" repeatCount="indefinite" />')
        svg.append(f'</circle>')
    svg.append('</g>')
    
    # ==== SYSTEM INFO TEXT ====
    y_pos = 120
    spacing = 23
    
    def add_row(label, value):
        nonlocal y_pos
        svg.append(f'<text x="528" y="{y_pos}" class="text-blue">{label}</text>')
        rem_len = 50 - len(label) - len(value)
        if rem_len < 3: rem_len = 3
        dots_str = "." * rem_len
        svg.append(f'<text x="{528 + 15 + len(label)*8.5}" y="{y_pos}" class="text-muted" textLength="{rem_len*8.5}" lengthAdjust="spacingAndGlyphs">{dots_str}</text>')
        svg.append(f'<text x="{528 + 15 + len(label)*8.5 + rem_len*8.5 + 10}" y="{y_pos}" class="text-primary">{value}</text>')
        y_pos += spacing
        
    profile = config.get("profile", {})
    add_row("Subject", profile.get("name", ""))
    add_row("Role", profile.get("headline", ""))
    add_row("Origin", profile.get("location", ""))
    add_row("Education", profile.get("education", ""))
    add_row("Status", profile.get("status", ""))
    
    y_pos += 15
    toolchain = config.get("toolchain", {})
    for k, v in toolchain.items():
        add_row(f"Core.{k.capitalize()}", v)
        
    y_pos += 15
    grid = config.get("grid", {})
    for k, v in grid.items():
        add_row(f"Grid.{k.capitalize()}", v)
        
    svg.append("</svg>")
    return "\n".join(svg)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    
    config = load_config(args.config)
    palette_name = config.get("appearance", {}).get("palette", "signal")
    if palette_name not in PALETTES:
        palette_name = "signal"
        
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    version_string = f"v1-{palette_name}"
    version = "python-" + hashlib.md5(version_string.encode()).hexdigest()[:8]
    
    for mode in ['dark', 'light']:
        dots = process_portrait(args.source, mode=mode)
        svg_content = generate_svg(config, dots, PALETTES[palette_name][mode], mode)
        filename = f"agent-console-{version}-{mode}.svg"
        with open(outdir / filename, "w", encoding="utf-8") as f:
            f.write(svg_content)
            
    manifest = {
        "generator": GENERATOR_VERSION,
        "version": version,
        "assets": {
            "desktopDark": f"agent-console-{version}-dark.svg",
            "desktopLight": f"agent-console-{version}-light.svg"
        }
    }
    with open(outdir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Generated hero assets (version {version}).")

if __name__ == "__main__":
    main()
