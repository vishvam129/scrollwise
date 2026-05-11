"""Pull facts from miscellaneous free public APIs (no keys required).

Sources:
- uselessfacts.jsph.pl    (random facts, English)
- numbersapi.com           (number/date/year facts)
- opentdb.com              (trivia, converted to fact statements)

Outputs: data/raw/misc_apis.json
"""

from __future__ import annotations

import html
import json
import random
import time
from pathlib import Path

import requests
from tqdm import tqdm

OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "misc_apis.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

USELESS_URL = "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"
NUMBERS_URL = "http://numbersapi.com/random/{kind}?json"
TRIVIA_URL = "https://opentdb.com/api.php?amount=50&type=multiple"

USELESS_COUNT = 2000
NUMBERS_PER_KIND = 1000  # trivia, math, date, year
TRIVIA_BATCHES = 100  # 50 per batch = 5000


def fetch_useless(n: int) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    pbar = tqdm(total=n, desc="useless facts")
    while len(out) < n:
        try:
            r = requests.get(USELESS_URL, timeout=15)
            r.raise_for_status()
            data = r.json()
            text = (data.get("text") or "").strip()
            fid = data.get("id")
            if not text or fid in seen:
                continue
            seen.add(fid)
            out.append(
                {
                    "id": f"useless_{fid}",
                    "source": "uselessfacts",
                    "text": text,
                }
            )
            pbar.update(1)
        except Exception:
            time.sleep(1)
        time.sleep(0.2)
    pbar.close()
    return out


def fetch_numbers() -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for kind in ["trivia", "math", "date", "year"]:
        pbar = tqdm(total=NUMBERS_PER_KIND, desc=f"numbers/{kind}")
        attempts = 0
        while (
            len([x for x in out if x["kind"] == kind]) < NUMBERS_PER_KIND
            and attempts < NUMBERS_PER_KIND * 3
        ):
            try:
                r = requests.get(NUMBERS_URL.format(kind=kind), timeout=15)
                r.raise_for_status()
                data = r.json()
                text = (data.get("text") or "").strip()
                if not text or text in seen:
                    attempts += 1
                    continue
                seen.add(text)
                out.append(
                    {
                        "id": f"num_{kind}_{data.get('number')}",
                        "source": "numbersapi",
                        "kind": kind,
                        "text": text,
                    }
                )
                pbar.update(1)
            except Exception:
                time.sleep(1)
            attempts += 1
            time.sleep(0.1)
        pbar.close()
    return out


def fetch_trivia() -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    pbar = tqdm(total=TRIVIA_BATCHES, desc="trivia")
    for _ in range(TRIVIA_BATCHES):
        try:
            r = requests.get(TRIVIA_URL, timeout=15)
            r.raise_for_status()
            data = r.json().get("results", [])
            for item in data:
                q = html.unescape(item.get("question", "")).strip()
                a = html.unescape(item.get("correct_answer", "")).strip()
                cat = item.get("category", "Trivia")
                if not q or not a:
                    continue
                # turn Q+A into a fact-style statement
                text = f"{q} Answer: {a}."
                if text in seen:
                    continue
                seen.add(text)
                out.append(
                    {
                        "id": f"trivia_{random.randint(0, 10**12)}",
                        "source": "opentdb",
                        "category_hint": cat,
                        "text": text,
                    }
                )
        except Exception:
            time.sleep(2)
        pbar.update(1)
        time.sleep(5.5)  # opentdb rate-limits to ~1 req / 5s
    pbar.close()
    return out


def main() -> None:
    facts: list[dict] = []
    facts += fetch_useless(USELESS_COUNT)
    facts += fetch_numbers()
    facts += fetch_trivia()
    OUT.write_text(json.dumps(facts, ensure_ascii=False, indent=2))
    print(f"\nSaved {len(facts)} misc-API facts -> {OUT}")


if __name__ == "__main__":
    main()
