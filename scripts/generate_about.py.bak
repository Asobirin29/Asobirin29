#!/usr/bin/env python3
"""
Generate About Me terminal SVG (blue theme) for GitHub profile.
This creates a beautiful blue-themed terminal that displays bio, skills, and contact info.
"""
import sys
import json
import argparse
import hashlib
from pathlib import Path

GENERATOR_VERSION = "about-terminal-v2-neon"

PALETTES = {
    "dark": {
        "bg":         "#0A0505",
        "bg_panel":   "#120505",
        "border":     "#E11D48",   # neon rose/red border
        "title":      "#FDA4AF",
        "label":      "#FB7185",
        "value":      "#F8FAFC",
        "muted":      "#64748B",
        "header_sep": "#4C0519",
        "cursor":     "#FDA4AF",
        "green_dot":  "#27c93f",
        "yellow_dot": "#ffbd2e",
        "red_dot":    "#ff5f56",
        "section":    "#BE123C",
        "section_txt":"#FECDD3",
    },
    "light": {
        "bg":         "#FFF1F2",
        "bg_panel":   "#FFE4E6",
        "border":     "#E11D48",
        "title":      "#BE123C",
        "label":      "#E11D48",
        "value":      "#4C0519",
        "muted":      "#94A3B8",
        "header_sep": "#FECDD3",
        "cursor":     "#E11D48",
        "green_dot":  "#16a34a",
        "yellow_dot": "#ca8a04",
        "red_dot":    "#dc2626",
        "section":    "#BE123C",
        "section_txt":"#881337",
    }
}

def build_about_svg(config, palette, mode):
    p = palette
    w, h = 1180, 610

    profile = config.get("profile", {})
    toolchain = config.get("toolchain", {})
    grid = config.get("grid", {})
    about_lines = profile.get("about", [])
    projects = config.get("projects", [])[:3]  # top 3 projects
    research = config.get("research", {})
    focus = config.get("focus", [])

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')

    # Defs: gradients, filters
    lines.append(f"""<defs>
  <linearGradient id="abg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{p['bg']}"/>
    <stop offset="1" stop-color="{p['bg_panel']}"/>
  </linearGradient>
  <linearGradient id="aaccent" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#E11D48"><animate attributeName="stop-color" values="#E11D48;#F43F5E;#FB7185;#E11D48" dur="8s" repeatCount="indefinite"/></stop>
    <stop offset="0.5" stop-color="#F43F5E"><animate attributeName="stop-color" values="#F43F5E;#FB7185;#E11D48;#F43F5E" dur="8s" repeatCount="indefinite"/></stop>
    <stop offset="1" stop-color="#FB7185"><animate attributeName="stop-color" values="#FB7185;#E11D48;#F43F5E;#FB7185" dur="8s" repeatCount="indefinite"/></stop>
  </linearGradient>
  <filter id="aglow3" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="3"/></filter>
  <filter id="aglow8" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="8"/></filter>
  <clipPath id="awinClip"><rect x="2" y="2" width="1176" height="606" rx="18"/></clipPath>
</defs>""")

    # Background
    lines.append(f'<rect x="2" y="2" width="1176" height="606" rx="18" fill="{p["bg"]}"/>')
    lines.append(f'<g clip-path="url(#awinClip)">')
    lines.append(f'<rect x="2" y="2" width="1176" height="606" fill="url(#abg)"/>')

    # Title bar
    lines.append(f'<rect x="2" y="2" width="1176" height="46" fill="#0B1222"/>')
    lines.append(f'<line x1="2" y1="48" x2="1178" y2="48" stroke="rgba(255,255,255,0.08)"/>')

    # Mac dots
    lines.append(f'<circle cx="30" cy="25" r="5.5" fill="{p["red_dot"]}"/>')
    lines.append(f'<circle cx="50" cy="25" r="5.5" fill="{p["yellow_dot"]}"/>')
    lines.append(f'<circle cx="70" cy="25" r="5.5" fill="{p["green_dot"]}"/>')

    # Title
    username = profile.get("username", "user")
    name = profile.get("name", "Developer")
    lines.append(f'<text x="590" y="29" text-anchor="middle" font-family="monospace" font-size="12" fill="{p["muted"]}">{username}@github.local - % ./about.sh --interactive</text>')

    # ── LEFT PANEL: About section ──────────────────────────────────────────
    lx, ly_top, lw, lh = 36, 60, 448, 526
    lines.append(f'<text x="{lx+2}" y="{ly_top-2}" font-family="monospace" font-size="10" letter-spacing="3" fill="{p["muted"]}">ABOUT.ME</text>')
    lines.append(f'<rect x="{lx}" y="{ly_top+4}" width="{lw}" height="{lh}" rx="10" fill="none" stroke="{p["border"]}" stroke-width="2" opacity="0.45" filter="url(#aglow3)"/>')
    lines.append(f'<rect x="{lx}" y="{ly_top+4}" width="{lw}" height="{lh}" rx="10" fill="{p["bg_panel"]}" stroke="{p["border"]}" stroke-opacity="0.30"/>')

    cy = ly_top + 34
    delay = 0.1

    import html
    def safe_text(val):
        return html.escape(str(val))

    def animated_text(x, y, content, fill, font_size=13, bold=False, delay_s=0.0, monospace=True):
        fw = "700" if bold else "400"
        ff = "monospace" if monospace else "sans-serif"
        safe_content = safe_text(content)
        lines.append(
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="{delay_s:.2f}s" fill="freeze"/>'
            f'<text x="{x}" y="{y}" font-family="{ff}" font-size="{font_size}" font-weight="{fw}" fill="{fill}">{safe_content}</text>'
            f'</g>'
        )

    def animated_row_left(label, value, y_pos, delay_s):
        safe_label = safe_text(label)
        safe_val = safe_text(value)
        lines.append(
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="{delay_s:.2f}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" values="-6 0;0 0" dur="0.4s" begin="{delay_s:.2f}s" fill="freeze"/>'
            f'<text x="{lx+16}" y="{y_pos}" font-family="monospace" font-size="13" xml:space="preserve">'
            f'<tspan fill="{p["label"]}">{safe_label} </tspan>'
            f'<tspan fill="{p["muted"]}" opacity="0.4">.....</tspan>'
            f'<tspan fill="{p["value"]}"> {safe_val}</tspan>'
            f'</text></g>'
        )

    # Name + Role header
    animated_text(lx+16, cy, f"# {name}", p["title"], font_size=16, bold=True, delay_s=delay)
    cy += 22; delay += 0.1
    animated_text(lx+16, cy, profile.get("headline", ""), p["label"], font_size=13, delay_s=delay)
    cy += 6; delay += 0.08

    # Separator
    lines.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="{delay:.2f}s" fill="freeze"/>'
                 f'<line x1="{lx+16}" y1="{cy+6}" x2="{lx+lw-16}" y2="{cy+6}" stroke="{p["border"]}" stroke-opacity="0.35"/></g>')
    cy += 18; delay += 0.08

    # About paragraphs
    for para in about_lines[:2]:
        # Word-wrap into ~55 char chunks
        words = para.split()
        cur_line = ""
        for word in words:
            if len(cur_line) + len(word) + 1 > 52:
                animated_text(lx+16, cy, cur_line, p["value"], font_size=12, delay_s=delay)
                cy += 17; delay += 0.04
                cur_line = word
            else:
                cur_line = (cur_line + " " + word).strip()
        if cur_line:
            animated_text(lx+16, cy, cur_line, p["value"], font_size=12, delay_s=delay)
            cy += 17; delay += 0.04
        cy += 4

    cy += 6
    # Section: quick stats
    animated_text(lx+16, cy, "[ STATS ]", p["section_txt"], font_size=11, bold=True, delay_s=delay)
    cy += 18; delay += 0.1

    animated_row_left("Location", profile.get("location",""), cy, delay); cy += 20; delay += 0.1
    animated_row_left("Education", profile.get("education",""), cy, delay); cy += 20; delay += 0.1
    animated_row_left("Status", profile.get("status",""), cy, delay); cy += 20; delay += 0.1

    cy += 6
    animated_text(lx+16, cy, "[ FOCUS ]", p["section_txt"], font_size=11, bold=True, delay_s=delay)
    cy += 18; delay += 0.1

    for f_item in focus[:3]:
        animated_text(lx+16, cy, f'▸ {f_item["name"]}', p["label"], font_size=12, bold=True, delay_s=delay)
        cy += 15; delay += 0.06
        # wrap description
        desc = f_item.get("description","")
        words = desc.split()
        cur_line = "  "
        for word in words:
            if len(cur_line) + len(word) + 1 > 52:
                animated_text(lx+20, cy, cur_line.strip(), p["muted"], font_size=11, delay_s=delay)
                cy += 14; delay += 0.03
                cur_line = "  " + word
            else:
                cur_line = (cur_line + " " + word)
        if cur_line.strip():
            animated_text(lx+20, cy, cur_line.strip(), p["muted"], font_size=11, delay_s=delay)
            cy += 14; delay += 0.03
        cy += 4

    # ── RIGHT PANEL: Skills & Contact ─────────────────────────────────────
    rx, ry_top, rw, rh = 502, 60, 650, 526
    lines.append(f'<text x="{rx+2}" y="{ry_top-2}" font-family="monospace" font-size="10" letter-spacing="3" fill="{p["muted"]}">SYSTEM.STACK</text>')
    lines.append(f'<rect x="{rx}" y="{ry_top+4}" width="{rw}" height="{rh}" rx="10" fill="none" stroke="{p["border"]}" stroke-width="2" opacity="0.45" filter="url(#aglow3)"/>')
    lines.append(f'<rect x="{rx}" y="{ry_top+4}" width="{rw}" height="{rh}" rx="10" fill="{p["bg_panel"]}" stroke="{p["border"]}" stroke-opacity="0.30"/>')

    rcy = ry_top + 30

    def animated_row_right(label, value, y_pos, d):
        safe_label = safe_text(label)
        safe_val = safe_text(value)
        lines.append(
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="{d:.2f}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" values="-8 0;0 0" dur="0.4s" begin="{d:.2f}s" fill="freeze"/>'
            f'<text x="{rx+16}" y="{y_pos}" font-family="monospace" font-size="13" textLength="{rw-32}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
            f'<tspan fill="{p["label"]}">{safe_label} </tspan>'
            f'<tspan fill="{p["muted"]}" opacity="0.35">..........................................................</tspan>'
            f'<tspan fill="{p["value"]}" font-weight="600"> {safe_val}</tspan>'
            f'</text></g>'
        )

    def section_header_right(title, y_pos, d):
        safe_title = safe_text(title)
        lines.append(
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="{d:.2f}s" fill="freeze"/>'
            f'<text x="{rx+16}" y="{y_pos}" font-family="monospace" font-size="13" textLength="{rw-32}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
            f'<tspan fill="{p["muted"]}">- {safe_title} </tspan>'
            f'<tspan fill="{p["muted"]}" opacity="0.35">-------------------------------------------------------------------</tspan>'
            f'</text></g>'
        )

    # Toolchain
    section_header_right("Toolchain", rcy, delay); rcy += 22; delay += 0.1
    for k, v in toolchain.items():
        animated_row_right(f"Core.{k.capitalize()}", v, rcy, delay); rcy += 21; delay += 0.1

    rcy += 8
    # Contact / Grid
    section_header_right("Links", rcy, delay); rcy += 22; delay += 0.1
    for k, v in grid.items():
        animated_row_right(f"Grid.{k.capitalize()}", v, rcy, delay); rcy += 21; delay += 0.1

    rcy += 8
    # Projects
    section_header_right("Projects", rcy, delay); rcy += 22; delay += 0.1
    for proj in projects:
        animated_row_right(f"Proj.{proj['name'][:12]}", proj.get("heroLabel",""), rcy, delay)
        rcy += 21; delay += 0.1

    rcy += 8
    # Research
    section_header_right("Research", rcy, delay); rcy += 22; delay += 0.1
    animated_row_right("Research.Area", research.get("primary",""), rcy, delay); rcy += 21; delay += 0.1
    animated_row_right("Research.Dir", research.get("direction",""), rcy, delay); rcy += 21; delay += 0.1

    # Cursor blink at end
    delay += 0.2
    lines.append(
        f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{delay:.2f}s" fill="freeze"/>'
        f'<text x="{rx+16}" y="{rcy+10}" font-family="monospace" font-size="13" fill="{p["muted"]}">'
        f'&#9656; Type <tspan fill="{p["label"]}">help</tspan> for commands'
        f' <tspan fill="{p["cursor"]}">&#9608;<animate attributeName="fill-opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></tspan>'
        f'</text></g>'
    )

    lines.append('</g>')  # end clip

    # Outer glow border
    lines.append(f'<rect x="3" y="3" width="1174" height="604" rx="17" fill="none" stroke="url(#aaccent)" stroke-width="3" opacity="0.55" filter="url(#aglow8)"/>')
    lines.append(f'<rect x="3" y="3" width="1174" height="604" rx="17" fill="none" stroke="url(#aaccent)" stroke-width="1.6"/>')

    lines.append('</svg>')
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate About Me terminal SVG")
    parser.add_argument("--config", required=True)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Hash config for versioning
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

    # Write manifest
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
