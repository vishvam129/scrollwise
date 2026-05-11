"""Scrape r/todayilearned across ~10 years using pullpush.io (Pushshift mirror).

Walks backwards month-by-month from today to ~2015, pulling top submissions.
Outputs: data/raw/reddit_til.json
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from tqdm import tqdm

PULLPUSH = "https://api.pullpush.io/reddit/submission/search/"
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "reddit_til.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

# 10-year window
END = int(datetime.now(tz=timezone.utc).timestamp())
START = int(datetime(2015, 1, 1, tzinfo=timezone.utc).timestamp())

PAGE_SIZE = 100
SLEEP = 1.0  # be polite


def fetch_window(before: int, after: int) -> list[dict]:
    params = {
        "subreddit": "todayilearned",
        "size": PAGE_SIZE,
        "before": before,
        "after": after,
        "sort": "desc",
        "sort_type": "score",
    }
    try:
        r = requests.get(PULLPUSH, params=params, timeout=30)
        r.raise_for_status()
        return r.json().get("data", [])
    except Exception as e:
        print(f"  ! request failed: {e}")
        return []


def main() -> None:
    seen: set[str] = set()
    facts: list[dict] = []

    # walk back in ~30-day chunks
    chunk = 30 * 24 * 60 * 60
    cursor = END
    total_windows = (END - START) // chunk

    pbar = tqdm(total=total_windows, desc="reddit TIL months")
    while cursor > START:
        after = max(cursor - chunk, START)
        batch = fetch_window(cursor, after)
        for post in batch:
            pid = post.get("id")
            title = (post.get("title") or "").strip()
            if not pid or not title or pid in seen:
                continue
            if not title.lower().startswith("til"):
                continue
            seen.add(pid)
            facts.append(
                {
                    "id": f"til_{pid}",
                    "source": "reddit_til",
                    "text": title,
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "score": post.get("score", 0),
                    "created_utc": post.get("created_utc"),
                }
            )
        cursor = after
        pbar.update(1)
        pbar.set_postfix(collected=len(facts))
        time.sleep(SLEEP)
    pbar.close()

    OUT.write_text(json.dumps(facts, ensure_ascii=False, indent=2))
    print(f"\nSaved {len(facts)} TIL posts -> {OUT}")


if __name__ == "__main__":
    main()
