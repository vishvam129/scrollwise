# Generator

One-time scripts that pull ~10 years of public facts from free sources (no API keys), then merge, dedupe, and categorize them into `data/facts.json` for the app.

## Sources
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
# raw scrape (each writes to data/raw/)
python generator/scrape_reddit_til.py        # ~1-2 hours (rate-limited)
python generator/scrape_wikipedia_dyk.py     # ~10-15 minutes
python generator/scrape_apis.py              # ~10-15 minutes

# merge + dedupe + categorize -> data/facts.json
python generator/merge_and_categorize.py
```

## Output

- `data/raw/reddit_til.json`
- `data/raw/wikipedia_dyk.json`
- `data/raw/misc_apis.json`
- `data/facts.json`  ← what the app reads

Expected total: **20,000–50,000 unique facts** across ~15 categories.

## Re-running

Scripts overwrite their output files on each run. Safe to re-run any time.
