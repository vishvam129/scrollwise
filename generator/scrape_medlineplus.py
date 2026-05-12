"""Scrape MedlinePlus health topics (NIH).

MedlinePlus publishes its full topic database as XML at
https://medlineplus.gov/xml.html — mplus_topics_<lang>_<date>.xml
This script discovers the latest English dump, downloads it, and extracts
title + summary for every topic. Content is US-government public domain.

Output: data/raw/medlineplus.json
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

INDEX = "https://medlineplus.gov/xml.html"
HEADERS = {"User-Agent": "scrollwise-scraper/0.1 (personal project)"}
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "medlineplus.json"
OUT.parent.mkdir(parents=True, exist_ok=True)


def find_latest_english_dump() -> str:
    r = requests.get(INDEX, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    candidates: list[str] = []
    for a in soup.select("a[href]"):
        href = a["href"]
        # Files look like: https://medlineplus.gov/xml/mplus_topics_YYYY-MM-DD.xml
        if "mplus_topics_" in href and href.endswith(".xml") and "groups" not in href:
            if not href.startswith("http"):
                href = "https://medlineplus.gov" + (
                    href if href.startswith("/") else "/" + href
                )
            candidates.append(href)
    if not candidates:
        raise RuntimeError(
            "Could not find a MedlinePlus topics XML dump on the index page."
        )
    # newest sorts to the end by ISO date in the filename
    return sorted(candidates)[-1]


def strip_html(text: str) -> str:
    soup = BeautifulSoup(text or "", "lxml")
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


def main() -> None:
    url = find_latest_english_dump()
    print(f"Downloading {url}")
    r = requests.get(url, headers=HEADERS, timeout=120)
    r.raise_for_status()

    root = ET.fromstring(r.content)
    facts: list[dict] = []
    seen: set[str] = set()
    topics = list(root.iter("health-topic"))
    pbar = tqdm(total=len(topics), desc="medlineplus")
    for topic in topics:
        title = (topic.get("title") or "").strip()
        summary_el = topic.find("full-summary")
        if summary_el is None:
            pbar.update(1)
            continue
        detail = strip_html(summary_el.text or "")
        if len(detail) > 800:
            detail = detail[:800].rsplit(" ", 1)[0] + "…"
        if not title or not detail or title.lower() in seen:
            pbar.update(1)
            continue
        seen.add(title.lower())
        facts.append(
            {
                "id": f"mp_{len(facts)}",
                "source": "medlineplus",
                "category": "Human Body",
                "title": title,
                "detail": detail,
                "url": topic.get("url"),
            }
        )
        pbar.update(1)
    pbar.close()

    OUT.write_text(json.dumps(facts, ensure_ascii=False, indent=2))
    print(f"\nSaved {len(facts)} MedlinePlus topics -> {OUT}")


if __name__ == "__main__":
    main()
