"""Scrape Wikipedia 'Did You Know?' archives across ~10 years.

Pages live at: https://en.wikipedia.org/wiki/Wikipedia:Recent_additions/<YEAR>/<MONTH>
Outputs: data/raw/wikipedia_dyk.json
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE = "https://en.wikipedia.org/wiki/Wikipedia:Recent_additions"
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "wikipedia_dyk.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

MONTHS = [
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
YEARS = list(range(2015, 2027))

HEADERS = {"User-Agent": "scrollwise-scraper/0.1 (personal project)"}
SLEEP = 0.5


def parse_page(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    out: list[str] = []
    for li in soup.select("div.mw-parser-output ul li"):
        text = li.get_text(" ", strip=True)
        if not text.startswith("... that"):
            continue
        # strip leading "... that " and trailing wiki cruft
        text = text[len("... that ") :].strip()
        text = re.sub(r"\s*\(pictured\)\s*", " ", text)
        text = re.sub(r"\s+", " ", text)
        if len(text) < 30 or len(text) > 400:
            continue
        # capitalize first letter, ensure trailing period
        text = text[0].upper() + text[1:]
        if not text.endswith("."):
            text += "."
        out.append(text)
    return out


def main() -> None:
    facts: list[dict] = []
    seen: set[str] = set()
    pbar = tqdm(total=len(YEARS) * len(MONTHS), desc="wikipedia DYK")
    for year in YEARS:
        for month in MONTHS:
            url = f"{BASE}/{year}/{month}"
            try:
                r = requests.get(url, headers=HEADERS, timeout=30)
                if r.status_code == 200:
                    for text in parse_page(r.text):
                        if text in seen:
                            continue
                        seen.add(text)
                        facts.append(
                            {
                                "id": f"dyk_{year}_{month}_{len(facts)}",
                                "source": "wikipedia_dyk",
                                "text": text,
                                "url": url,
                                "year": year,
                                "month": month,
                            }
                        )
            except Exception as e:
                print(f"  ! {url} -> {e}")
            pbar.update(1)
            pbar.set_postfix(collected=len(facts))
            time.sleep(SLEEP)
    pbar.close()

    OUT.write_text(json.dumps(facts, ensure_ascii=False, indent=2))
    print(f"\nSaved {len(facts)} DYK facts -> {OUT}")


if __name__ == "__main__":
    main()
