# Generator

One-time scripts that pull ~10 years of public facts from free sources (no API keys), then merge, dedupe, and categorize them into `data/facts.json` for the app.

## Sources
- **Wikipedia article intros** (curated topics across 12 categories, deep on Human Body) — highest-quality, already in title+detail shape
- **Reddit r/todayilearned** (via pullpush.io mirror) — ~10 years of top posts
- **Wikipedia "Did You Know?"** archives — monthly DYK pages 2015–present
- **uselessfacts.jsph.pl** — random English facts
- **numbersapi.com** — number, math, date, year facts
- **opentdb.com** — trivia Q&A converted to fact statements

## Setup

```bash
cd ~/Desktop/scrollwise
python3 -m venv venv
source venv/bin/activate
pip install -r generator/requirements.txt
```

## Run (order matters only for merge step)

The three scrapers are independent — you can run them in parallel terminals if you want.

```bash
# raw scrape (each writes to data/raw/) — run in any order, can be parallel
python generator/scrape_wikipedia_topics.py  # ~3-5 min (best source, already has detail)
python generator/scrape_reddit_til.py        # ~1-2 hours (rate-limited)
python generator/scrape_wikipedia_dyk.py     # ~10-15 minutes
python generator/scrape_apis.py              # ~15-25 minutes

# merge + dedupe + categorize -> data/facts.json
python generator/merge_and_categorize.py

# (optional) enrich each fact with a 2-3 sentence Gemini-generated explanation
python generator/enrich_with_gemini.py
```

## Output

- `data/raw/reddit_til.json`
- `data/raw/wikipedia_dyk.json`
- `data/raw/misc_apis.json`
- `data/facts.json`  ← what the app reads

Expected total: **20,000–50,000 unique facts** across ~15 categories.

## Re-running

Scripts overwrite their output files on each run. Safe to re-run any time.
