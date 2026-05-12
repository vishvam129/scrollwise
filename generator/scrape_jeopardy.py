"""Download the public Jeopardy clue dataset and reformat as facts.

Source: https://github.com/jwolle1/jeopardy_clue_dataset (~538k clues, public)
The repo ships TSV files like `combined_season1-XX.tsv` in the root; we use
the GitHub Contents API to find the largest TSV and download it.

Each clue has: category, answer (the prompt shown on screen), question (the
contestant's response — i.e., the real fact). We turn it into:
    title  = the real fact (contestant's response)
    detail = "Jeopardy clue (<category>): '<prompt>'"

Output: data/raw/jeopardy.json
"""

from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path

import requests
from tqdm import tqdm

CONTENTS_API = "https://api.github.com/repos/jwolle1/jeopardy_clue_dataset/contents/"
HEADERS = {"User-Agent": "scrollwise-scraper/0.1 (personal project)"}
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "jeopardy.json"
OUT.parent.mkdir(parents=True, exist_ok=True)


def find_largest_tsv() -> tuple[str, int]:
    r = requests.get(CONTENTS_API, headers=HEADERS, timeout=30)
    r.raise_for_status()
    files = [
        f
        for f in r.json()
        if f.get("name", "").endswith(".tsv") and f.get("type") == "file"
    ]
    if not files:
        raise RuntimeError("No TSV files found in jeopardy_clue_dataset root.")
    files.sort(key=lambda f: f.get("size", 0), reverse=True)
    top = files[0]
    return top["download_url"], top.get("size", 0)


def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def main() -> None:
    url, size = find_largest_tsv()
    print(f"Downloading {url} ({size / 1024 / 1024:.1f} MB)")
    r = requests.get(url, headers=HEADERS, timeout=300)
    r.raise_for_status()
    text = r.text

    # detect dialect
    sample = "\n".join(text.splitlines()[:5])
    delim = "\t" if "\t" in sample else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    rows = list(reader)
    print(f"Parsed {len(rows)} rows")

    facts: list[dict] = []
    seen: set[str] = set()
    pbar = tqdm(total=len(rows), desc="jeopardy")
    for row in rows:
        # column names vary between dataset versions; handle the common ones
        cat = clean(row.get("category") or row.get("Category") or "")
        answer = clean(row.get("answer") or row.get("Answer") or row.get("clue") or "")
        question = clean(
            row.get("question") or row.get("Question") or row.get("response") or ""
        )
        if not answer or not question or len(question) < 2:
            pbar.update(1)
            continue
        # in Jeopardy: "answer" = the prompt, "question" = the contestant response
        title = question
        detail = (
            f"From a Jeopardy! clue in the category '{cat}': \"{answer}\""
            if cat
            else f'Jeopardy! clue: "{answer}"'
        )
        key = re.sub(r"[^a-z0-9]", "", title.lower())[:120]
        if not key or key in seen:
            pbar.update(1)
            continue
        seen.add(key)
        facts.append(
            {
                "id": f"jp_{len(facts)}",
                "source": "jeopardy",
                "category_hint": cat,
                "title": title,
                "detail": detail,
            }
        )
        pbar.update(1)
    pbar.close()

    OUT.write_text(json.dumps(facts, ensure_ascii=False))
    print(f"\nSaved {len(facts)} Jeopardy clues -> {OUT}")


if __name__ == "__main__":
    main()
