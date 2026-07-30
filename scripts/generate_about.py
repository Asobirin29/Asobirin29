#!/usr/bin/env python3
"""
Generate About Me terminal SVG (RPG theme) for GitHub profile.
This creates a retro RPG-style status screen with pixel art.
"""
import sys
import json
import argparse
import hashlib
from pathlib import Path

GENERATOR_VERSION = "about-terminal-v4-rpg-red"

PALETTES = {
    "dark": {
        "bg":         "#2D0404",   # Deep blood red
        "bg_panel":   "#3F0808",
        "border_out": "#7F1D1D",   # Dark red border
        "border_in":  "#EF4444",   # Bright red inner
        "title":      "#FCA5A5",
        "label":      "#F87171",
        "value":      "#FEF2F2",
        "muted":      "#FCA5A5",
        "section":    "#991B1B",
        "section_txt":"#FEF2F2",
        "cursor":     "#EF4444",
    },
    "light": {
        "bg":         "#FEE2E2",
        "bg_panel":   "#FECACA",
        "border_out": "#991B1B",
        "border_in":  "#DC2626",
        "title":      "#7F1D1D",
        "label":      "#991B1B",
        "value":      "#450A0A",
        "muted":      "#7F1D1D",
        "section":    "#EF4444",
        "section_txt":"#FEF2F2",
        "cursor":     "#DC2626",
    }
}

def draw_sprite(x, y, scale, pixels, colors):
    svg = []
    for row_idx, row in enumerate(pixels):
        for col_idx, char in enumerate(row):
            if char in colors:
                svg.append(f'<rect x="{x + col_idx * scale}" y="{y + row_idx * scale}" width="{scale}" height="{scale}" fill="{colors[char]}"/>')
    return "".join(svg)

# Sprite definitions
SWORD_PIXELS = [
    "       X",
    "      XXX",
    "     XXX ",
    "    XXX  ",
    "   XXX   ",
    "  XXX    ",
    " XXX     ",
    " YYX     ",
    "YYY      ",
    " YY      "
]

KNIGHT_PIXELS = [
    "   RRR   ",
    "  RRRR   ",
    "   XX    ",
    "  XXXX   ",
    "  X XX   ",
    "  XXXXX  ",
    "   XXX   ",
    "  XXXXX  ",
    " XX X XX ",
    " X  X  X ",
    "    X    ",
    "   XXX   ",
    "   X X   ",
    "  XX XX  "
]

MONSTER_PIXELS = [
    "   M  M   ",
    "  MMMMMM  ",
    " MMMMMMMM ",
    " MMYMMYMM ",
    " MMMMMMMM ",
    "  MMMMMM  ",
    "  M    M  ",
    "  MM  MM  "
]

def build_about_svg(config, palette, mode):
    p = palette
    w, h = 1180, 630

    profile = config.get("profile", {})
    toolchain = config.get("toolchain", {})
    grid = config.get("grid", {})
    about_lines = profile.get("about", [])
    projects = config.get("projects", [])[:3]
    research = config.get("research", {})
    focus = config.get("focus", [])

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')

    lines.append(f"""<defs>
  <filter id="rpg-shadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="4" dy="4" stdDeviation="2" flood-color="#000000" flood-opacity="0.6"/>
  </filter>
  <filter id="gold-glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="3" result="blur" />
    <feComposite in="SourceGraphic" in2="blur" operator="over" />
  </filter>
  <pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="2" fill="#000000" opacity="0.15" />
  </pattern>
</defs>""")

    # Background Box
    lines.append(f'<rect x="10" y="10" width="1160" height="610" rx="8" fill="{p["bg"]}" stroke="{p["border_out"]}" stroke-width="6" filter="url(#rpg-shadow)"/>')
    lines.append(f'<rect x="18" y="18" width="1144" height="594" rx="4" fill="none" stroke="{p["border_in"]}" stroke-width="2"/>')
    
    if mode == "dark":
        lines.append(f'<rect x="20" y="20" width="1140" height="590" fill="url(#scanlines)" pointer-events="none" opacity="0.4"/>')

    # RPG Header
    name = profile.get("name", "Hero")
    lines.append(f'<rect x="440" y="6" width="300" height="34" fill="{p["bg"]}" stroke="{p["border_out"]}" stroke-width="4" rx="4"/>')
    lines.append(f'<text x="590" y="29" text-anchor="middle" font-family="monospace" font-weight="bold" font-size="16" fill="{p["title"]}" letter-spacing="2">CHARACTER STATUS</text>')

    import html
    def safe_text(val):
        return html.escape(str(val))

    def animated_text(x, y, content, fill, font_size=14, bold=False, delay_s=0.0):
        fw = "700" if bold else "400"
        safe_content = safe_text(content)
        lines.append(
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="{delay_s:.2f}s" fill="freeze"/>'
            f'<text x="{x}" y="{y}" font-family="monospace" font-size="{font_size}" font-weight="{fw}" fill="{fill}">{safe_content}</text>'
            f'</g>'
        )

    def section_title(x, y, text, delay_s):
        lines.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="{delay_s:.2f}s" fill="freeze"/>')
        lines.append(f'<rect x="{x}" y="{y-14}" width="220" height="20" fill="{p["section"]}" rx="2"/>')
        lines.append(f'<text x="{x+6}" y="{y}" font-family="monospace" font-size="13" font-weight="bold" fill="{p["section_txt"]}">{safe_text(text)}</text>')
        lines.append(f'</g>')

    def animated_row(x, y, label, value, delay_s, w_limit=450):
        safe_label = safe_text(label)
        safe_val = safe_text(value)
        lines.append(
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="{delay_s:.2f}s" fill="freeze"/>'
            f'<text x="{x}" y="{y}" font-family="monospace" font-size="14" xml:space="preserve">'
            f'<tspan fill="{p["label"]}" font-weight="bold">{safe_label}</tspan>'
            f'<tspan fill="{p["muted"]}" opacity="0.6"> : </tspan>'
            f'<tspan fill="{p["value"]}">{safe_val}</tspan>'
            f'</text></g>'
        )

    # Render Pixel Art
    sword_colors = {"X": "#E2E8F0", "Y": "#FBBF24"} if mode == "dark" else {"X": "#94A3B8", "Y": "#D97706"}
    knight_colors = {"R": "#FBBF24", "X": "#E2E8F0"} if mode == "dark" else {"R": "#D97706", "X": "#94A3B8"}
    monster_colors = {"M": "#A855F7", "Y": "#FBBF24"}
    
    # Add sprites to SVG
    lines.append('<g opacity="0.8">')
    lines.append(draw_sprite(430, 80, 4, KNIGHT_PIXELS, knight_colors))
    lines.append(draw_sprite(440, 200, 3, MONSTER_PIXELS, monster_colors))
    lines.append(draw_sprite(1000, 80, 4, SWORD_PIXELS, sword_colors))
    lines.append('</g>')

    lx, cy, lw = 40, 70, 520
    delay = 0.2

    # LEFT PANEL
    animated_text(lx, cy, f"▶ {name.upper()}", p["title"], font_size=20, bold=True, delay_s=delay); cy += 24; delay += 0.1
    animated_text(lx+20, cy, f"Class: {profile.get('headline', 'Adventurer')} (Lv. 99)", p["value"], font_size=14, delay_s=delay); cy += 24; delay += 0.1
    animated_row(lx+20, cy, "Current Quest", profile.get("status",""), delay); cy += 20; delay += 0.1
    animated_row(lx+20, cy, "Base Area", profile.get("location",""), delay); cy += 20; delay += 0.1
    animated_row(lx+20, cy, "Training", profile.get("education",""), delay); cy += 24; delay += 0.1

    lines.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.3s" begin="{delay:.2f}s" fill="freeze"/>'
                 f'<line x1="{lx}" y1="{cy}" x2="{lx+lw}" y2="{cy}" stroke="{p["border_in"]}" stroke-opacity="0.5" stroke-dasharray="4,4"/></g>')
    cy += 24; delay += 0.1

    section_title(lx, cy, "LORE / BACKGROUND", delay); cy += 20; delay += 0.1
    for para in about_lines[:2]:
        words = para.split()
        cur_line = ""
        for word in words:
            if len(cur_line) + len(word) + 1 > 55:
                animated_text(lx+10, cy, cur_line, p["value"], font_size=13, delay_s=delay)
                cy += 18; delay += 0.05
                cur_line = word
            else:
                cur_line = (cur_line + " " + word).strip()
        if cur_line:
            animated_text(lx+10, cy, cur_line, p["value"], font_size=13, delay_s=delay)
            cy += 18; delay += 0.05
        cy += 8

    cy += 8
    section_title(lx, cy, "SKILL TREE / FOCUS", delay); cy += 20; delay += 0.1
    for f_item in focus[:3]:
        animated_text(lx+10, cy, f'✦ {f_item["name"]}', p["label"], font_size=14, bold=True, delay_s=delay)
        cy += 18; delay += 0.06
        
        desc = f_item.get("description","")
        words = desc.split()
        cur_line = "  "
        for word in words:
            if len(cur_line) + len(word) + 1 > 55:
                animated_text(lx+20, cy, cur_line.strip(), p["muted"], font_size=12, delay_s=delay)
                cy += 16; delay += 0.04
                cur_line = "  " + word
            else:
                cur_line = (cur_line + " " + word)
        if cur_line.strip():
            animated_text(lx+20, cy, cur_line.strip(), p["muted"], font_size=12, delay_s=delay)
            cy += 16; delay += 0.04
        cy += 8


    # RIGHT PANEL
    rx, rcy, rw = 600, 70, 520

    section_title(rx, rcy, "EQUIPPED TECH (MAGIC)", delay); rcy += 24; delay += 0.1
    for k, v in toolchain.items():
        animated_row(rx+10, rcy, k.capitalize().ljust(9), v, delay); rcy += 20; delay += 0.1

    rcy += 12
    section_title(rx, rcy, "ALLIED GUILDS (LINKS)", delay); rcy += 24; delay += 0.1
    for k, v in grid.items():
        animated_row(rx+10, rcy, k.capitalize().ljust(9), v, delay); rcy += 20; delay += 0.1

    rcy += 12
    section_title(rx, rcy, "COMPLETED CAMPAIGNS", delay); rcy += 24; delay += 0.1
    for proj in projects:
        animated_row(rx+10, rcy, proj['name'][:12].ljust(12), proj.get("heroLabel",""), delay)
        rcy += 20; delay += 0.1

    rcy += 12
    section_title(rx, rcy, "ARCANE RESEARCH", delay); rcy += 24; delay += 0.1
    animated_row(rx+10, rcy, "Area".ljust(9), research.get("primary",""), delay); rcy += 20; delay += 0.1
    animated_row(rx+10, rcy, "Direction".ljust(9), research.get("direction",""), delay); rcy += 20; delay += 0.1

    delay += 0.3
    lines.append(
        f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{delay:.2f}s" fill="freeze"/>'
        f'<text x="590" y="580" text-anchor="middle" font-family="monospace" font-size="18" fill="{p["cursor"]}" filter="url(#gold-glow)">'
        f'▼'
        f'<animate attributeName="y" values="580; 585; 580" dur="1s" repeatCount="indefinite"/>'
        f'</text></g>'
    )

    lines.append('</svg>')
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Generate About Me terminal SVG (RPG Theme)")
    parser.add_argument("--config", required=True)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    config_hash = hashlib.md5((json.dumps(config, sort_keys=True) + GENERATOR_VERSION).encode()).hexdigest()[:8]
    version = f"about-{config_hash}"

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for mode in ["dark", "light"]:
        svg = build_about_svg(config, PALETTES[mode], mode)
        filename = f"about-terminal-{config_hash}-{mode}.svg"
        out_path = outdir / filename
        out_path.write_text(svg, encoding="utf-8")
        print(f"Generated: {filename}")

    manifest = {
        "version": version,
        "assets": {
            "dark": f"about-terminal-{config_hash}-dark.svg",
            "light": f"about-terminal-{config_hash}-light.svg",
        }
    }
    (outdir / "about-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"About terminal generated (version {version}).")

if __name__ == "__main__":
    main()
