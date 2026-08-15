"""
make_ascii_svg.py
Converts data/source-prepped.png into an animated ASCII portrait SVG.

Pipeline:
  1. Load preprocessed grayscale image (data/source-prepped.png)
  2. Sample pixel grid at ASCII resolution (cols x rows)
  3. Map brightness -> ASCII density character
  4. Generate SVG with monospace text elements
  5. Apply row-by-row left-to-right reveal animation (plays once, freezes)

Output: charan-ascii.svg
Usage:  python scripts/make_ascii_svg.py
"""

import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("Install with: pip install -r scripts/requirements-local.txt")
    sys.exit(1)

INPUT_PATH = Path(__file__).parent.parent / "data" / "source-prepped.png"
OUTPUT_PATH = Path(__file__).parent.parent / "charan-ascii.svg"

# ─── ASCII Configuration ────────────────────────────────────────────────────
# Density ramp: left = bright (sparse), right = dark (dense)
RAMP = " .`:-=+*cs#%@"
RAMP_LEN = len(RAMP)

ASCII_COLS = 90      # characters per row (80-120 range)
# Row count derived from image aspect ratio + char compensation

# ─── SVG Typography ─────────────────────────────────────────────────────────
CHAR_W = 7.2         # px per character (monospace at font-size 12)
CHAR_H = 13          # px per line
FONT_SIZE = 12
FONT = "'SF Mono', 'Fira Code', 'Cascadia Code', monospace"

# ─── Colors ─────────────────────────────────────────────────────────────────
BG_COLOR = "#0d1117"
ASCII_COLOR = "#c9d1d9"    # light gray — professional, not rainbow

# ─── Padding ────────────────────────────────────────────────────────────────
PAD_X = 16
PAD_Y = 16

# ─── Animation ──────────────────────────────────────────────────────────────
# Row-by-row reveal, plays once, freezes at end
ROW_DELAY_BASE = 0.3      # seconds before first row appears
ROW_DELAY_STEP = 0.04     # seconds per row stagger
ROW_DURATION = 0.2        # seconds per row fade-in


def load_image():
    if not INPUT_PATH.exists():
        print(f"[ERROR] Preprocessed image not found: {INPUT_PATH}")
        print("        Run first: python scripts/prep_photo.py <photo-path>")
        sys.exit(1)

    img = Image.open(INPUT_PATH)

    # Ensure grayscale
    if img.mode != "L":
        img = img.convert("L")

    print(f"[INFO]  Loaded preprocessed image: {img.size[0]}x{img.size[1]}")
    return img


def image_to_ascii_grid(img):
    """
    Resample the image to ASCII_COLS x ASCII_ROWS resolution.
    Returns a 2D list of ASCII characters.
    """
    # Compute rows based on aspect ratio with char aspect compensation
    # Characters are roughly 2:1 H:W, so we need fewer rows
    char_aspect = CHAR_H / CHAR_W  # ~1.8
    img_aspect = img.height / img.width
    ascii_rows = int(ASCII_COLS * img_aspect / char_aspect)
    ascii_rows = max(ascii_rows, 20)

    print(f"[INFO]  ASCII grid: {ASCII_COLS} cols x {ascii_rows} rows")

    # Resize image to exactly the character grid dimensions
    small = img.resize((ASCII_COLS, ascii_rows), Image.LANCZOS)
    pixels = np.array(small)  # shape: (rows, cols), dtype uint8

    grid = []
    for row in pixels:
        row_chars = []
        for brightness in row:
            # Invert: bright pixels -> sparse, dark pixels -> dense
            # brightness 0=black, 255=white
            # We want white background -> space, dark subject -> dense chars
            index = int((brightness / 255.0) * (RAMP_LEN - 1))
            index = max(0, min(RAMP_LEN - 1, index))
            row_chars.append(RAMP[index])
        grid.append(row_chars)

    return grid


def escape_xml(ch):
    """Escape special XML characters."""
    return ch.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_svg(grid):
    rows = len(grid)
    cols = len(grid[0]) if grid else 0

    # SVG canvas size
    content_w = cols * CHAR_W
    content_h = rows * CHAR_H
    svg_w = int(content_w + PAD_X * 2)
    svg_h = int(content_h + PAD_Y * 2)

    lines = []

    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{svg_w}" height="{svg_h}" '
        f'viewBox="0 0 {svg_w} {svg_h}" '
        f'role="img" '
        f'aria-label="Animated ASCII portrait of Charan Sai Yalla">'
    )

    # Background
    lines.append(f'<rect width="{svg_w}" height="{svg_h}" fill="{BG_COLOR}"/>')

    # Monospace font definition
    lines.append(
        f'<style>'
        f'.ascii-row {{ font-family: {FONT}; font-size: {FONT_SIZE}px; '
        f'fill: {ASCII_COLOR}; white-space: pre; }}'
        f'</style>'
    )

    # One <text> element per row with animation
    for row_idx, row_chars in enumerate(grid):
        y = PAD_Y + (row_idx + 1) * CHAR_H
        x = PAD_X

        row_text = "".join(row_chars)

        # Skip completely empty rows (all spaces) — saves SVG nodes
        if row_text.strip() == "":
            continue

        delay = round(ROW_DELAY_BASE + row_idx * ROW_DELAY_STEP, 3)
        dur = ROW_DURATION

        # Clip path for left-to-right wipe effect
        clip_id = f"clip-r{row_idx}"
        clip_x = x
        clip_y = y - CHAR_H
        clip_h = CHAR_H + 2
        clip_w_full = int(content_w)

        lines.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="{clip_x}" y="{clip_y}" width="0" height="{clip_h}">'
            f'<animate attributeName="width" '
            f'from="0" to="{clip_w_full}" '
            f'begin="{delay}s" dur="{dur}s" '
            f'fill="freeze" calcMode="spline" '
            f'keySplines="0.4 0 0.2 1"/>'
            f'</rect>'
            f'</clipPath>'
        )

        # Text row with clip + fade
        lines.append(
            f'<text x="{x}" y="{y}" class="ascii-row" '
            f'clip-path="url(#{clip_id})" '
            f'opacity="0">'
            f'{escape_xml(row_text)}'
            f'<animate attributeName="opacity" '
            f'from="0" to="1" '
            f'begin="{delay}s" dur="{dur}s" fill="freeze"/>'
            f'</text>'
        )

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    print("[INFO]  Loading preprocessed image ...")
    img = load_image()

    print("[INFO]  Converting to ASCII grid ...")
    grid = image_to_ascii_grid(img)

    print("[INFO]  Rendering animated SVG ...")
    svg_content = render_svg(grid)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg_content)

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    rows = len(grid)
    cols = len(grid[0]) if grid else 0
    print(f"[OK]    ASCII grid: {cols}x{rows} characters")
    print(f"[OK]    Saved to {OUTPUT_PATH} ({size_kb:.1f} KB)")
    print("[DONE]  make_ascii_svg.py complete.")


if __name__ == "__main__":
    main()
