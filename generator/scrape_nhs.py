"""Scrape NHS conditions A-Z and Live Well pages.

NHS content is published under the Open Government Licence v3, free to reuse with attribution.
Each condition page has a clean intro paragraph that maps to our title + detail schema.

Output: data/raw/nhs.json
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE = "https://www.nhs.uk"
INDEXES = [
    "/conditions/",
    "/live-well/sexual-health/",
    "/pregnancy/",
    "/mental-health/",
    "/conditions/contraception/",
]
HEADERS = {
    "User-Agent": "scrollwise-scraper/0.1 (personal project; contact: dev@scrollwise.local)"
}
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "nhs.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
SLEEP = 0.7


def discover_links(index_path: str) -> list[str]:
    """Pull all article links from an NHS index page (A-Z listings)."""
    url = BASE + index_path
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"  ! index {url}: {e}")
        return []
    soup = BeautifulSoup(r.text, "lxml")
    links: set[str] = set()
    for a in soup.select("a[href]"):
        href = a["href"]
        if (
            href.startswith("/conditions/")
            or href.startswith("/live-well/")
            or href.startswith("/pregnancy/")
        ):
            # skip the index pages themselves and anchors
            if href.rstrip("/") == index_path.rstrip("/"):
                continue
            if "#" in href:
                href = href.split("#", 1)[0]
            links.add(href)
    return sorted(links)


def parse_article(html: str) -> tuple[str, str] | None:
    soup = BeautifulSoup(html, "lxml")
    h1 = soup.select_one("h1")
    title = (h1.get_text(" ", strip=True) if h1 else "").strip()
    # NHS articles usually have a lede paragraph inside <main>
    main = soup.select_one("main") or soup
    paragraphs: list[str] = []
    for p in main.select("p"):
        text = p.get_text(" ", strip=True)
        if len(text) < 40:
            continue
        # skip navigation / unrelated boilerplate
        if any(
            s in text.lower()
            for s in ("cookie", "privacy", "nhs app", "find your local")
        ):
            continue
        paragraphs.append(text)
        if len(paragraphs) >= 3:
            break
    if not title or not paragraphs:
        return None
    detail = " ".join(paragraphs)
    detail = re.sub(r"\s+", " ", detail).strip()
    if len(detail) > 800:
        detail = detail[:800].rsplit(" ", 1)[0] + "…"
    return title, detail


def main() -> None:
    all_links: set[str] = set()
    for idx in INDEXES:
        for href in discover_links(idx):
            all_links.add(href)
    print(f"Discovered {len(all_links)} NHS article links")

    facts: list[dict] = []
    seen_titles: set[str] = set()
    pbar = tqdm(total=len(all_links), desc="nhs articles")
    for href in sorted(all_links):
        url = BASE + href
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code != 200:
                pbar.update(1)
                continue
            parsed = parse_article(r.text)
            if not parsed:
                pbar.update(1)
                continue
            title, detail = parsed
            key = title.lower()
            if key in seen_titles:
                pbar.update(1)
                continue
            seen_titles.add(key)
            facts.append(
                {
                    "id": f"nhs_{len(facts)}",
                    "source": "nhs",
                    "category": "Human Body",
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
    print(f"\nSaved {len(facts)} NHS articles -> {OUT}")


if __name__ == "__main__":
    main()
