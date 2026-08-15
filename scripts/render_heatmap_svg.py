"""
render_heatmap_svg.py
Reads data/contributions.json and renders an animated SVG contribution heatmap.
Uses GitHub-inspired color palette with SVG-native SMIL animation.
No JavaScript. No external resources.

Output: contrib-heatmap.svg
Usage:  python scripts/render_heatmap_svg.py
"""

import json
import sys
import math
from datetime import datetime, date, timedelta
from pathlib import Path

INPUT_PATH = Path(__file__).parent.parent / "data" / "contributions.json"
OUTPUT_PATH = Path(__file__).parent.parent / "contrib-heatmap.svg"

# GitHub-inspired contribution color palette
PALETTE = [
    "#161b22",  # level 0 — no contribution
    "#0e4429",  # level 1 — low
    "#006d32",  # level 2 — medium-low
    "#26a641",  # level 3 — medium
    "#39d353",  # level 4 — high
]

CELL_SIZE = 11       # px per cell
CELL_GAP = 3         # px gap between cells
CELL_RADIUS = 2      # rounded corners
WEEK_STRIDE = CELL_SIZE + CELL_GAP
DAY_STRIDE = CELL_SIZE + CELL_GAP

# Layout constants
MARGIN_LEFT = 28     # space for day-of-week labels
MARGIN_TOP = 24      # space for month labels
MARGIN_BOTTOM = 36   # space for legend
MARGIN_RIGHT = 16

WEEKS = 53
DAYS = 7

SVG_WIDTH = MARGIN_LEFT + WEEKS * WEEK_STRIDE + MARGIN_RIGHT
SVG_HEIGHT = MARGIN_TOP + DAYS * DAY_STRIDE + MARGIN_BOTTOM

MONTH_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]
DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]  # alternating for cleanliness

TEXT_COLOR = "#8b949e"
BORDER_COLOR = "#30363d"
BG_COLOR = "#0d1117"
GREEN_PRIMARY = "#39d353"


def load_data():
    if not INPUT_PATH.exists():
        print(f"[ERROR] Input file not found: {INPUT_PATH}")
        print("        Run: python scripts/fetch_contributions.py")
        sys.exit(1)

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in {INPUT_PATH}: {e}")
            sys.exit(1)

    if "days" not in data or not data["days"]:
        print("[ERROR] contributions.json is empty or malformed.")
        sys.exit(1)

    return data


def build_day_map(days):
    """Build a dict of date_str -> (count, level)."""
    return {d["date"]: (d["count"], d["level"]) for d in days}


def get_grid_start(days):
    """Compute the Sunday that starts the 53-week grid ending today."""
    today = date.today()
    # Find the most recent Saturday (end of last complete week + today's week)
    days_since_sunday = today.weekday() + 1  # Mon=0 so Sun offset = weekday+1
    if days_since_sunday == 7:
        days_since_sunday = 0
    grid_end = today + timedelta(days=(6 - days_since_sunday))
    grid_start = grid_end - timedelta(weeks=WEEKS) + timedelta(days=1)
    # Align to Sunday
    while grid_start.weekday() != 6:  # 6 = Sunday
        grid_start -= timedelta(days=1)
    return grid_start


def level_color(level):
    level = max(0, min(4, level))
    return PALETTE[level]


def animation_delay(week, day, total_weeks=WEEKS, total_days=DAYS):
    """Diagonal reveal: delay proportional to week + day."""
    # Total animation time ~2.5s, stagger 0.04s per diagonal step
    diagonal = week + day
    max_diagonal = total_weeks + total_days - 2
    delay = 0.3 + (diagonal / max_diagonal) * 2.0
    return round(delay, 3)


def render_svg(data):
    day_map = build_day_map(data["days"])
    stats = data.get("stats", {})
    grid_start = get_grid_start(data["days"])

    lines = []

    # SVG header
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{SVG_WIDTH}" height="{SVG_HEIGHT}" '
        f'viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}" '
        f'role="img" '
        f'aria-label="GitHub contribution heatmap for charansaiyalla">'
    )

    # Background
    lines.append(
        f'<rect width="{SVG_WIDTH}" height="{SVG_HEIGHT}" '
        f'rx="6" ry="6" fill="{BG_COLOR}"/>'
    )

    # Month labels
    month_positions = {}
    for week in range(WEEKS):
        col_date = grid_start + timedelta(weeks=week)
        month_key = col_date.month
        if month_key not in month_positions:
            month_positions[month_key] = week
    for month, week_idx in month_positions.items():
        x = MARGIN_LEFT + week_idx * WEEK_STRIDE
        y = MARGIN_TOP - 6
        label = MONTH_LABELS[month - 1]
        lines.append(
            f'<text x="{x}" y="{y}" '
            f'font-family="\'SF Mono\', \'Fira Code\', monospace" '
            f'font-size="9" fill="{TEXT_COLOR}" '
            f'letter-spacing="0.5">{label}</text>'
        )

    # Day-of-week labels
    for day_idx, label in enumerate(DAY_LABELS):
        if not label:
            continue
        x = MARGIN_LEFT - 4
        y = MARGIN_TOP + day_idx * DAY_STRIDE + CELL_SIZE - 1
        lines.append(
            f'<text x="{x}" y="{y}" '
            f'font-family="\'SF Mono\', \'Fira Code\', monospace" '
            f'font-size="9" fill="{TEXT_COLOR}" '
            f'text-anchor="end">{label}</text>'
        )

    # Contribution cells with diagonal reveal animation
    for week in range(WEEKS):
        for day in range(DAYS):  # 0=Sun ... 6=Sat
            cell_date = grid_start + timedelta(weeks=week, days=day)
            date_str = cell_date.isoformat()
            today = date.today()

            if cell_date > today:
                color = BG_COLOR
                count = 0
                level = 0
            elif date_str in day_map:
                count, level = day_map[date_str]
                color = level_color(level)
            else:
                color = PALETTE[0]
                count = 0
                level = 0

            x = MARGIN_LEFT + week * WEEK_STRIDE
            y = MARGIN_TOP + day * DAY_STRIDE

            delay = animation_delay(week, day)
            duration = 0.25

            title = (
                f"{count} contribution{'s' if count != 1 else ''} on "
                f"{cell_date.strftime('%B %-d, %Y') if sys.platform != 'win32' else cell_date.strftime('%B %d, %Y')}"
                if count > 0 else
                f"No contributions on {cell_date.strftime('%B %d, %Y')}"
            )

            lines.append(
                f'<rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
                f'rx="{CELL_RADIUS}" ry="{CELL_RADIUS}" '
                f'fill="{color}" '
                f'data-date="{date_str}" data-level="{level}">'
                f'<title>{title}</title>'
                f'<animate attributeName="opacity" '
                f'from="0" to="1" '
                f'begin="{delay}s" dur="{duration}s" '
                f'fill="freeze" calcMode="spline" '
                f'keySplines="0.4 0 0.2 1"/>'
                f'<animate attributeName="rx" '
                f'from="6" to="{CELL_RADIUS}" '
                f'begin="{delay}s" dur="{duration}s" '
                f'fill="freeze"/>'
                f'</rect>'
            )

    # Stats bar
    stats_y = MARGIN_TOP + DAYS * DAY_STRIDE + 14
    total = stats.get("total", 0)
    current_streak = stats.get("current_streak", 0)
    longest_streak = stats.get("longest_streak", 0)

    if total > 0:
        stats_text = f"{total} contributions in the last year"
        if current_streak > 0:
            stats_text += f"  ·  Current streak: {current_streak}d"
        if longest_streak > 0:
            stats_text += f"  ·  Longest: {longest_streak}d"
        lines.append(
            f'<text x="{MARGIN_LEFT}" y="{stats_y}" '
            f'font-family="\'SF Mono\', \'Fira Code\', monospace" '
            f'font-size="10" fill="{TEXT_COLOR}">{stats_text}</text>'
        )

    # Legend
    legend_x_start = SVG_WIDTH - MARGIN_RIGHT - 6 * (CELL_SIZE + CELL_GAP) - 50
    legend_y = stats_y + 14

    lines.append(
        f'<text x="{legend_x_start - 4}" y="{legend_y + 8}" '
        f'font-family="\'SF Mono\', \'Fira Code\', monospace" '
        f'font-size="9" fill="{TEXT_COLOR}" text-anchor="end">Less</text>'
    )
    for i, color in enumerate(PALETTE):
        lx = legend_x_start + i * (CELL_SIZE + CELL_GAP)
        lines.append(
            f'<rect x="{lx}" y="{legend_y}" '
            f'width="{CELL_SIZE}" height="{CELL_SIZE}" '
            f'rx="{CELL_RADIUS}" ry="{CELL_RADIUS}" fill="{color}"/>'
        )
    more_x = legend_x_start + len(PALETTE) * (CELL_SIZE + CELL_GAP) + 4
    lines.append(
        f'<text x="{more_x}" y="{legend_y + 8}" '
        f'font-family="\'SF Mono\', \'Fira Code\', monospace" '
        f'font-size="9" fill="{TEXT_COLOR}">More</text>'
    )

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    print("[INFO]  Loading contribution data ...")
    data = load_data()
    print(f"[INFO]  Loaded {len(data['days'])} days of contribution data.")

    print("[INFO]  Rendering heatmap SVG ...")
    svg_content = render_svg(data)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg_content)

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"[OK]    Saved to {OUTPUT_PATH} ({size_kb:.1f} KB)")
    print("[DONE]  render_heatmap_svg.py complete.")


if __name__ == "__main__":
    main()
