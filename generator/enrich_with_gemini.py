"""Enrich facts.json by asking Gemini to write a short 'detail' paragraph for each fact.

Reads:  data/facts.json
Writes: data/facts.json (in place, with `detail` populated)

- Batches N facts per API call to save quota.
- Checkpoints after every batch so it resumes safely on crash.
- Skips facts that already have a non-empty detail.

Setup:
    pip install google-generativeai python-dotenv
    # GEMINI_API_KEY must be set in scrollwise/.env.local
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
FACTS = ROOT / "data" / "facts.json"

load_dotenv(ROOT / ".env.local")
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise SystemExit("GEMINI_API_KEY not set in .env.local")

import google.generativeai as genai  # noqa: E402

genai.configure(api_key=API_KEY)
MODEL = genai.GenerativeModel("gemini-2.0-flash")

BATCH_SIZE = 15  # facts per API call
SLEEP = 4.5  # ~13 req/min, under the 15 RPM free-tier limit


PROMPT_TEMPLATE = """You are writing short, engaging explanations for a "scroll facts instead of doomscrolling" app.

For each numbered fact below, write a 2-3 sentence "detail" that explains the fact with extra context, surprising depth, or why it matters. Keep the tone curious and conversational. Do NOT repeat the original fact verbatim — assume the reader already saw it as a headline.

Output STRICT JSON: an array of objects, each shaped like {{"id": "<id from input>", "detail": "<your 2-3 sentences>"}}. Output ONLY the JSON, no markdown fences, no commentary.

FACTS:
{facts}
"""


def build_prompt(batch: list[dict]) -> str:
    lines = []
    for f in batch:
        lines.append(f"- id: {f['id']}\n  fact: {f['title']}")
    return PROMPT_TEMPLATE.format(facts="\n".join(lines))


def parse_response(text: str) -> list[dict]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip("` \n")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # try to salvage: find first '[' and last ']'
        start = text.find("[")
        end = text.rfind("]")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def enrich_batch(batch: list[dict]) -> dict[str, str]:
    prompt = build_prompt(batch)
    resp = MODEL.generate_content(prompt)
    items = parse_response(resp.text)
    return {it["id"]: it["detail"] for it in items if it.get("id") and it.get("detail")}


def main() -> None:
    facts: list[dict] = json.loads(FACTS.read_text())
    todo = [f for f in facts if not f.get("detail")]
    print(f"Total facts: {len(facts)} | needing detail: {len(todo)}")

    by_id = {f["id"]: f for f in facts}
    pbar = tqdm(total=len(todo), desc="enrich")

    for i in range(0, len(todo), BATCH_SIZE):
        batch = todo[i : i + BATCH_SIZE]
        try:
            details = enrich_batch(batch)
            for fid, detail in details.items():
                if fid in by_id:
                    by_id[fid]["detail"] = detail.strip()
            FACTS.write_text(json.dumps(facts, ensure_ascii=False, indent=2))
            pbar.update(len(batch))
        except Exception as e:
            print(f"\n  ! batch failed: {e}. sleeping 30s and continuing...")
            time.sleep(30)
        time.sleep(SLEEP)
    pbar.close()
    print(f"Done. {sum(1 for f in facts if f.get('detail'))}/{len(facts)} have detail.")


if __name__ == "__main__":
    main()
