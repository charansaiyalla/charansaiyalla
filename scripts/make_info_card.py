"""
make_info_card.py
Generates a neofetch-style animated SVG information card.
No JavaScript. No external resources. Pure SVG SMIL + embedded CSS animation.

Output: info-card.svg
Usage:  python scripts/make_info_card.py
        STATIC=1 python scripts/make_info_card.py   (no animation, for preview)
"""

import os
import sys
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent.parent / "info-card.svg"
STATIC_MODE = os.environ.get("STATIC", "0") == "1"

# ─── Color Palette ────────────────────────────────────────────────────────────
BG = "#0d1117"
BORDER = "#30363d"
GREEN = "#39d353"
GREEN_DIM = "#26a641"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
LABEL = "#58a6ff"

# ─── Card Dimensions ──────────────────────────────────────────────────────────
W = 480
FONT = "'SF Mono', 'Fira Code', 'Cascadia Code', monospace"

# ─── Profile Data ─────────────────────────────────────────────────────────────
SECTIONS = [
    # (label, value, color_override)
    ("USER",       "charan@github",              GREEN),
    ("SEPARATOR",  None,                          None),
    ("Name",       "Charan Sai Yalla",           TEXT),
    ("Role",       "CSE Student  /  Developer",  TEXT),
    ("Bio",        "Be the one, not just one among many.", MUTED),
    ("BLANK",      None,                          None),
    ("Languages",  "C++  Java  Python  JS  TS",  TEXT),
    ("Frontend",   "React  React Native  Vite",   TEXT),
    ("Backend",    "Node.js  Express  Spring Boot", TEXT),
    ("Database",   "PostgreSQL  Supabase  Prisma", TEXT),
    ("BLANK",      None,                          None),
    ("Focus",      "DSA  ·  Full Stack  ·  AI",  TEXT),
    ("BLANK",      None,                          None),
    ("Experience", "Agentic AI Intern",           TEXT),
    ("",           "Geethanjali College of Engg", MUTED),
    ("",           "May 2026 – Jun 2026",         MUTED),
    ("BLANK",      None,                          None),
    ("Status",     "Building  ·  Learning  ·  Solving", GREEN_DIM),
]

LINE_HEIGHT = 18
PADDING_X = 18
HEADER_H = 36
CONTENT_START_Y = HEADER_H + 14

def count_visible_lines():
    count = 0
    for (label, val, _) in SECTIONS:
        if label == "SEPARATOR":
            count += 1
        elif label == "BLANK":
            count += 1
        elif label == "USER":
            count += 1
        else:
            count += 1
    return count

def compute_height():
    lines = count_visible_lines()
    return CONTENT_START_Y + lines * LINE_HEIGHT + 20

def escape(s):
    return (s
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;"))

def make_animation(index, total, delay_base=0.8):
    if STATIC_MODE:
        return ""
    delay = round(delay_base + index * 0.08, 2)
    return (
        f'<animate attributeName="opacity" '
        f'from="0" to="1" '
        f'begin="{delay}s" dur="0.3s" fill="freeze" '
        f'calcMode="spline" keySplines="0.4 0 0.2 1"/>'
        f'<animate attributeName="y" '
        f'from="{{}}" to="{{}}" '
        f'begin="{delay}s" dur="0.3s" fill="freeze" '
        f'calcMode="spline" keySplines="0.4 0 0.2 1"/>'
    )


def render_svg():
    H = compute_height()
    total_lines = count_visible_lines()
    lines = []

    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'role="img" '
        f'aria-label="Neofetch-style developer info card for Charan Sai Yalla">'
    )

    # Background
    lines.append(f'<rect width="{W}" height="{H}" rx="6" fill="{BG}"/>')
    # Border
    lines.append(
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" '
        f'rx="6" fill="none" stroke="{BORDER}" stroke-width="1"/>'
    )

    # Header bar
    lines.append(
        f'<rect x="0" y="0" width="{W}" height="{HEADER_H}" '
        f'rx="6" fill="#161b22"/>'
    )
    lines.append(
        f'<rect x="0" y="{HEADER_H - 6}" width="{W}" height="6" '
        f'fill="#161b22"/>'
    )
    lines.append(
        f'<line x1="0" y1="{HEADER_H}" x2="{W}" y2="{HEADER_H}" '
        f'stroke="{BORDER}" stroke-width="1"/>'
    )

    # Traffic light dots
    for i, col in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        cx = 16 + i * 18
        cy = HEADER_H // 2
        lines.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="{col}"/>')

    # Terminal title
    lines.append(
        f'<text x="{W//2}" y="{HEADER_H//2 + 4}" '
        f'font-family="{FONT}" font-size="11" '
        f'fill="{MUTED}" text-anchor="middle" letter-spacing="1">'
        f'charan@github — system info'
        f'</text>'
    )

    # Content lines
    anim_index = 0
    y = CONTENT_START_Y

    for i, (label, value, color) in enumerate(SECTIONS):
        if label == "USER":
            # Username line with green prompt
            if STATIC_MODE:
                opacity = "1"
                anim = ""
            else:
                opacity = "0"
                delay = round(0.8 + anim_index * 0.08, 2)
                anim = (
                    f'<animate attributeName="opacity" from="0" to="1" '
                    f'begin="{delay}s" dur="0.3s" fill="freeze"/>'
                )
            lines.append(
                f'<text x="{PADDING_X}" y="{y}" '
                f'font-family="{FONT}" font-size="12" '
                f'fill="{GREEN}" opacity="{opacity}">'
                f'{escape(value)}{anim}</text>'
            )
            anim_index += 1
            y += LINE_HEIGHT

        elif label == "SEPARATOR":
            if STATIC_MODE:
                opacity = "1"
                anim = ""
            else:
                opacity = "0"
                delay = round(0.8 + anim_index * 0.08, 2)
                anim = (
                    f'<animate attributeName="opacity" from="0" to="1" '
                    f'begin="{delay}s" dur="0.3s" fill="freeze"/>'
                )
            sep_w = W - PADDING_X * 2
            lines.append(
                f'<line x1="{PADDING_X}" y1="{y}" x2="{PADDING_X + sep_w}" y2="{y}" '
                f'stroke="{GREEN}" stroke-width="1" opacity="{opacity}">'
                f'{anim}</line>'
            )
            anim_index += 1
            y += LINE_HEIGHT

        elif label == "BLANK":
            y += int(LINE_HEIGHT * 0.5)

        else:
            if STATIC_MODE:
                opacity = "1"
                anim = ""
            else:
                opacity = "0"
                delay = round(0.8 + anim_index * 0.08, 2)
                anim = (
                    f'<animate attributeName="opacity" from="0" to="1" '
                    f'begin="{delay}s" dur="0.3s" fill="freeze"/>'
                )

            if label:
                # Label portion
                label_w = 76
                lines.append(
                    f'<text x="{PADDING_X}" y="{y}" '
                    f'font-family="{FONT}" font-size="11" '
                    f'fill="{LABEL}" opacity="{opacity}">'
                    f'{escape(label)}{anim}</text>'
                )
                # Colon
                lines.append(
                    f'<text x="{PADDING_X + label_w}" y="{y}" '
                    f'font-family="{FONT}" font-size="11" '
                    f'fill="{MUTED}" opacity="{opacity}">'
                    f': {anim}</text>'
                )
                # Value
                lines.append(
                    f'<text x="{PADDING_X + label_w + 14}" y="{y}" '
                    f'font-family="{FONT}" font-size="11" '
                    f'fill="{escape(color or TEXT)}" opacity="{opacity}">'
                    f'{escape(value or "")}{anim}</text>'
                )
            else:
                # Continuation line (indented, no label)
                lines.append(
                    f'<text x="{PADDING_X + 76 + 14}" y="{y}" '
                    f'font-family="{FONT}" font-size="11" '
                    f'fill="{escape(color or MUTED)}" opacity="{opacity}">'
                    f'{escape(value or "")}{anim}</text>'
                )
            anim_index += 1
            y += LINE_HEIGHT

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    mode = "STATIC" if STATIC_MODE else "ANIMATED"
    print(f"[INFO]  Generating info card ({mode} mode) ...")

    svg_content = render_svg()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg_content)

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"[OK]    Saved to {OUTPUT_PATH} ({size_kb:.1f} KB)")
    print("[DONE]  make_info_card.py complete.")


if __name__ == "__main__":
    main()
