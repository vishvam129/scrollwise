"""Scrape Wikipedia 'On this day' across all 366 calendar days.

Uses the public Wikimedia REST endpoint, which returns events/births/deaths/
holidays/selected for the given MM/DD, each with a linked page extract.
No API key, CC BY-SA.

Output: data/raw/onthisday.json
"""

from __future__ import annotations

import calendar
import json
import re
import time
from pathlib import Path

import requests
from tqdm import tqdm

API = "https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/all/{mm:02d}/{dd:02d}"
HEADERS = {"User-Agent": "scrollwise-scraper/0.1 (personal project)"}
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "onthisday.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
SLEEP = 0.3

MONTH_NAME = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def shorten(text: str, limit: int = 700) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


def process_bucket(bucket: str, items: list[dict], mm: int, dd: int) -> list[dict]:
    out: list[dict] = []
    for it in items:
        year = it.get("year")
        text = (it.get("text") or "").strip()
        pages = it.get("pages") or []
        if not text:
            continue
        # title: 'On May 11, 1997: Deep Blue defeats Kasparov...'
        date_str = f"On {MONTH_NAME[mm]} {dd}"
        if year:
            date_str = f"{date_str}, {year}"
        title = f"{date_str}: {text}"
        # detail: best linked page extract
        detail = ""
        for p in pages:
            extract = (p.get("extract") or "").strip()
            if extract:
                detail = extract
                break
        detail = shorten(detail)
        out.append(
            {
                "id": f"otd_{mm:02d}_{dd:02d}_{bucket}_{len(out)}",
                "source": "onthisday",
                "category": "This Day in History",
                "title": shorten(title, 250),
                "detail": detail,
                "month": mm,
                "day": dd,
                "year": year,
                "bucket": bucket,
                "url": pages[0]["content_urls"]["desktop"]["page"]
                if pages and pages[0].get("content_urls")
                else None,
            }
        )
    return out


def main() -> None:
    facts: list[dict] = []
    seen: set[str] = set()
    days = [
        (m, d)
        for m in range(1, 13)
        for d in range(1, calendar.monthrange(2024, m)[1] + 1)
    ]
    pbar = tqdm(total=len(days), desc="on this day")
    for mm, dd in days:
        url = API.format(mm=mm, dd=dd)
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code != 200:
                pbar.update(1)
                time.sleep(SLEEP)
                continue
            data = r.json()
            for bucket in ("events", "births", "deaths", "holidays", "selected"):
                for f in process_bucket(bucket, data.get(bucket, []), mm, dd):
                    key = re.sub(r"[^a-z0-9]", "", f["title"].lower())[:140]
                    if key and key not in seen:
                        seen.add(key)
                        facts.append(f)
        except Exception as e:
            print(f"  ! {url}: {e}")
        pbar.update(1)
        pbar.set_postfix(collected=len(facts))
        time.sleep(SLEEP)
    pbar.close()

    OUT.write_text(json.dumps(facts, ensure_ascii=False, indent=2))
    print(f"\nSaved {len(facts)} On-this-day items -> {OUT}")


if __name__ == "__main__":
    main()
