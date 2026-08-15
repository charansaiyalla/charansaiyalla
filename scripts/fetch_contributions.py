"""
fetch_contributions.py
Scrapes contribution data from GitHub's public contribution calendar.
No GitHub token required. Uses only public HTML.

Output: data/contributions.json
Usage:  python scripts/fetch_contributions.py
"""

import json
import sys
import re
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("Install with: pip install -r scripts/requirements-ci.txt")
    sys.exit(1)

USERNAME = "charansaiyalla"
CONTRIBUTIONS_URL = f"https://github.com/users/{USERNAME}/contributions"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "contributions.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "X-Requested-With": "XMLHttpRequest",
}


def fetch_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
    except requests.exceptions.ConnectionError:
        print("[ERROR] Failed to connect to GitHub. Check your internet connection.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out after 15 seconds.")
        sys.exit(1)

    if response.status_code != 200:
        print(f"[ERROR] Failed to fetch GitHub contribution data.")
        print(f"        HTTP status: {response.status_code}")
        print(f"        URL: {url}")
        sys.exit(1)

    return response.text


def parse_contributions(html):
    soup = BeautifulSoup(html, "lxml")

    # Primary selector: td elements with data-date (current GitHub format)
    cells = soup.select("td[data-date]")

    if not cells:
        # Fallback: rect elements (older GitHub calendar format)
        cells = soup.select("rect[data-date]")

    if not cells:
        print("[ERROR] Could not locate contribution cells.")
        print("        GitHub contribution page structure may have changed.")
        sys.exit(1)

    days = []
    for cell in cells:
        date_str = cell.get("data-date", "").strip()
        if not date_str:
            continue

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue

        level_attr = cell.get("data-level", "0")
        try:
            level = int(level_attr)
        except (ValueError, TypeError):
            level = 0

        count = 0
        label = cell.get("aria-label", "") or cell.get("title", "")
        if label:
            match = re.search(r"(\d+)\s+contribution", label, re.IGNORECASE)
            if match:
                count = int(match.group(1))
            elif "no contributions" in label.lower():
                count = 0
            else:
                count = _level_to_estimate(level)
        else:
            count = _level_to_estimate(level)

        days.append({"date": date_str, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])

    if len(days) < 30:
        print(f"[ERROR] Only {len(days)} contribution cells found — expected 300+.")
        print("        Page structure may have changed or access was blocked.")
        sys.exit(1)

    print(f"[OK]    Parsed {len(days)} contribution days.")
    return days


def _level_to_estimate(level):
    return {0: 0, 1: 1, 2: 3, 3: 6, 4: 10}.get(level, 0)


def compute_stats(days):
    total = sum(d["count"] for d in days)
    best_day = max((d["count"] for d in days), default=0)

    today_str = date.today().isoformat()
    day_map = {d["date"]: d["count"] for d in days}

    current_streak = 0
    check_date = date.today()
    while True:
        ds = check_date.isoformat()
        if ds in day_map and day_map[ds] > 0:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            if ds == today_str and current_streak == 0:
                check_date -= timedelta(days=1)
                ds = check_date.isoformat()
                if ds in day_map and day_map[ds] > 0:
                    current_streak += 1
                    check_date -= timedelta(days=1)
                    continue
            break

    longest_streak = 0
    run = 0
    for d in days:
        if d["count"] > 0:
            run += 1
            longest_streak = max(longest_streak, run)
        else:
            run = 0

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
    }


def save_json(data):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK]    Saved to {OUTPUT_PATH}")


def main():
    print(f"[INFO]  Fetching contributions for @{USERNAME} ...")
    html = fetch_html(CONTRIBUTIONS_URL)
    days = parse_contributions(html)
    stats = compute_stats(days)

    output = {
        "username": USERNAME,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "days": days,
        "stats": stats,
    }

    save_json(output)

    print(f"[INFO]  Total contributions  : {stats['total']}")
    print(f"[INFO]  Current streak       : {stats['current_streak']} days")
    print(f"[INFO]  Longest streak       : {stats['longest_streak']} days")
    print(f"[INFO]  Best single day      : {stats['best_day']}")
    print("[DONE]  fetch_contributions.py complete.")


if __name__ == "__main__":
    main()
