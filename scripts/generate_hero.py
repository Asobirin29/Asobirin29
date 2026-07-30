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

def process_portrait(source_path, target_width=150, target_height=170, mode='dark'):
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
    
    # Base layout and styles matching arifhaxn's dark.svg
    svg.append(f"""
    <defs>
      <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="{palette['violet']}"><animate attributeName="stop-color" values="{palette['violet']};{palette['cyan']};{palette['green']};{palette['violet']}" dur="10s" repeatCount="indefinite"/></stop>
        <stop offset="0.5" stop-color="{palette['cyan']}"><animate attributeName="stop-color" values="{palette['cyan']};{palette['green']};{palette['violet']};{palette['cyan']}" dur="10s" repeatCount="indefinite"/></stop>
        <stop offset="1" stop-color="{palette['green']}"><animate attributeName="stop-color" values="{palette['green']};{palette['violet']};{palette['cyan']};{palette['green']}" dur="10s" repeatCount="indefinite"/></stop>
      </linearGradient>
      <linearGradient id="panelGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{palette['bg_start']}"/><stop offset="1" stop-color="{palette['bg_end']}"/></linearGradient>
      <filter id="glow8" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="8"/></filter>
      <filter id="glow3" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="3"/></filter>
      <clipPath id="winClip"><rect x="2" y="2" width="1176" height="606" rx="18"/></clipPath>
    </defs>
    
    <rect x="2" y="2" width="1176" height="606" rx="18" fill="#070B16"/>
    <g clip-path="url(#winClip)">
      <rect x="2" y="2" width="1176" height="606" fill="url(#panelGrad)"/>
      <rect x="2" y="2" width="1176" height="46" fill="#0B1222"/>
      <line x1="2" y1="48" x2="1178" y2="48" stroke="rgba(255,255,255,0.10)"/>
      
      <circle cx="30" cy="25.0" r="5.5" fill="#ff5f56"/>
      <circle cx="50" cy="25.0" r="5.5" fill="#ffbd2e"/>
      <circle cx="70" cy="25.0" r="5.5" fill="#27c93f"/>
      
      <text x="590.0" y="29.0" text-anchor="middle" font-family="monospace" font-size="12" fill="{palette['muted']}">user@github.local - % ./profile.sh --live</text>
      
      <text x="38" y="74" font-family="monospace" font-size="10" letter-spacing="3" fill="#475569">VISUAL.MAP</text>
      <rect x="36" y="84" width="400" height="492" rx="10" fill="none" stroke="{palette['cyan']}" stroke-width="2" opacity="0.45" filter="url(#glow3)"/>
      <rect x="36" y="84" width="400" height="492" rx="10" fill="{palette['bg_start']}" stroke="rgba(34,211,238,0.35)"/>
    """)
    
    # We apply a scale transformation for the portrait to fit nicely in the 400x492 frame.
    # The portrait points are generated assuming the top-left starts at 0,0 but we can just
    # wrap them in a group that scales and positions them correctly inside the frame.
    
    # Dots Processing
    coords = np.argwhere(dots) # [y, x]
    N = len(coords)
    
    # ==== INTRO LAYER ====
    # 60 interleaved random groups fade in over ~2s
    # Total time 3.2s. 
    intro_groups = 20
    # Center the dots inside the new 400x492 portrait frame at (36,84)
    # Dot field is 150x170. Scale up 2.3x to fill the frame nicely.
    svg.append(f'<g transform="translate(46, 96) scale(2.3, 2.3)" fill="{palette["violet"]}" shape-rendering="crispEdges">')
    for g in range(intro_groups):
        g_coords = coords[g::intro_groups]
        paths = []
        for y, x in g_coords:
            paths.append(f"M{x},{y}h1")
        path_str = " ".join(paths)
        fade_start = random.uniform(0.05, 1.5)
        path_str = " ".join(paths)
        svg.append(
            f'<g opacity="0">'
            f'<animate attributeName="opacity" values="0;1" dur="0.9s" begin="{fade_start:.2f}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".4 0 .2 1"/>'
            f'<path d="{path_str}" stroke="currentColor" stroke-width="1"/>'
            f'</g>'
        )
    svg.append('</g>')
    
    # Keep portrait visible after intro (simple approach, no loop/traveller for file size)
    # Portrait just stays at opacity=1 after fading in.
    # We use a simple set element to freeze state after intro.
    # (Loop and traveller layers removed to keep file size under GitHub Camo limit ~800KB)
    
    # ==== SYSTEM INFO TEXT ====
    # Using the beautiful animated rows from dark.svg
    y_pos = 120
    delay_start = 0.5
    
    svg.append(f'<g font-family="monospace">')
    svg.append(f'<text x="470" y="80" font-size="10" letter-spacing="3" fill="#475569">SYSTEM.INFO</text>')
    
    def add_animated_row(label, value, is_header=False):
        nonlocal y_pos, delay_start
        if is_header:
            svg.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="{delay_start:.2f}s" fill="freeze"/><text x="470" y="{y_pos}" font-size="14" textLength="655" lengthAdjust="spacingAndGlyphs" xml:space="preserve"><tspan fill="{palette["muted"]}">- {label} </tspan><tspan fill="{palette["muted"]}" opacity="0.35">---------------------------------------------------------------------</tspan></text></g>')
        else:
            svg.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="{delay_start:.2f}s" fill="freeze"/><animateTransform attributeName="transform" type="translate" values="-8 0;0 0" dur="0.4s" begin="{delay_start:.2f}s" fill="freeze"/><text x="470" y="{y_pos}" font-size="14" textLength="655" lengthAdjust="spacingAndGlyphs" xml:space="preserve"><tspan fill="{palette["cyan"]}">{label} </tspan><tspan fill="{palette["muted"]}" opacity="0.35">..........................................................</tspan><tspan fill="{palette["primary"]}" font-weight="600"> {value}</tspan></text></g>')
        y_pos += 23
        delay_start += 0.12
        
    profile = config.get("profile", {})
    add_animated_row("Subject", profile.get("name", "user"))
    add_animated_row("Role", profile.get("headline", ""))
    add_animated_row("Origin", profile.get("location", ""))
    add_animated_row("Education", profile.get("education", ""))
    add_animated_row("Status", profile.get("status", ""))
    
    y_pos += 8
    add_animated_row("Toolchain", "", is_header=True)
    toolchain = config.get("toolchain", {})
    for k, v in toolchain.items():
        add_animated_row(f"Core.{k.capitalize()}", v)
        
    y_pos += 8
    add_animated_row("Links", "", is_header=True)
    grid = config.get("grid", {})
    for k, v in grid.items():
        add_animated_row(f"Grid.{k.capitalize()}", v)
        
    # Final pulsing text
    delay_start += 0.2
    svg.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{delay_start:.2f}s" fill="freeze"/>')
    svg.append(f'<text x="470" y="{y_pos + 15}" font-size="14" fill="{palette["muted"]}">&#9656; Keep scrolling for more stats &amp; projects &#8595; <tspan fill="{palette["cyan"]}">&#9608;<animate attributeName="fill-opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></tspan></text>')
    svg.append('</g>')
    
    svg.append('</g>')
    
    svg.append('</g>') # close clip-path
    svg.append(f'<rect x="3" y="3" width="1174" height="604" rx="17" fill="none" stroke="url(#accent)" stroke-width="3" opacity="0.55" filter="url(#glow8)"/>')
    svg.append(f'<rect x="3" y="3" width="1174" height="604" rx="17" fill="none" stroke="url(#accent)" stroke-width="1.6"/>')
    
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
    
    import os
    source_mtime = str(int(os.path.getmtime(args.source)))
    version_string = f"v3-{palette_name}-{source_mtime}"
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
