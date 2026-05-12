"""Scrape NASA Astronomy Picture of the Day (1995-06-16 to today).

Uses the public archive at https://apod.nasa.gov/apod/archivepixFull.html which
lists every APOD entry as a link, then fetches each daily page and parses the
title + explanation. APOD content is US-government public domain.

Output: data/raw/nasa_apod.json
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE = "https://apod.nasa.gov/apod/"
ARCHIVE = BASE + "archivepixFull.html"
HEADERS = {"User-Agent": "scrollwise-scraper/0.1 (personal project)"}
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "nasa_apod.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
SLEEP = 0.3


def list_pages() -> list[str]:
    r = requests.get(ARCHIVE, headers=HEADERS, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    pages: list[str] = []
    for a in soup.select("a[href]"):
        href = a["href"]
        if re.fullmatch(r"ap\d{6}\.html", href):
            pages.append(href)
    # deduplicate while preserving order (newest-first as listed)
    seen: set[str] = set()
    out: list[str] = []
    for p in pages:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def parse_page(html: str) -> tuple[str, str] | None:
    soup = BeautifulSoup(html, "lxml")
    title_el = soup.select_one("b") or soup.select_one("center b")
    title = title_el.get_text(" ", strip=True) if title_el else ""
    # The explanation is usually preceded by a <b>Explanation:</b> tag.
    body = soup.get_text(" ", strip=True)
    m = re.search(
        r"Explanation:\s*(.+?)(?:Tomorrow's picture|Authors? & editors|<<)", body, re.S
    )
    if not m:
        return None
    detail = re.sub(r"\s+", " ", m.group(1)).strip()
    # cap length
    if len(detail) > 900:
        detail = detail[:900].rsplit(" ", 1)[0] + "…"
    if not title or len(detail) < 60:
        return None
    return title, detail


def main() -> None:
    pages = list_pages()
    print(f"Found {len(pages)} APOD entries")

    facts: list[dict] = []
    seen: set[str] = set()
    pbar = tqdm(total=len(pages), desc="apod")
    for page in pages:
        url = BASE + page
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code != 200:
                pbar.update(1)
                continue
            parsed = parse_page(r.text)
            if not parsed:
                pbar.update(1)
                continue
            title, detail = parsed
            key = title.lower()
            if key in seen:
                pbar.update(1)
                continue
            seen.add(key)
            facts.append(
                {
                    "id": f"apod_{page.replace('.html', '')}",
                    "source": "nasa_apod",
                    "category": "Space",
                    "title": title,
                    "detail": detail,
                    "url": url,
                }
            )
        except Exception as e:
            print(f"  ! {url}: {e}")
        pbar.update(1)
        pbar.set_postfix(collected=len(facts))
        time.sleep(SLEEP)
    pbar.close()

    OUT.write_text(json.dumps(facts, ensure_ascii=False, indent=2))
    print(f"\nSaved {len(facts)} APOD entries -> {OUT}")


if __name__ == "__main__":
    main()
