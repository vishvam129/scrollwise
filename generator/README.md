# Generator

Pulls millions of facts from free, licensed sources, then merges, dedupes, and categorizes them into `data/facts.json` for the app.

## Sources (all free, no API key required)

| Script | Source | License | Est. facts | Has detail? |
|---|---|---|---|---|
| `scrape_wikipedia_topics.py` | Curated Wikipedia article intros (deep Human Body) | CC BY-SA | ~270 | ✅ |
| `scrape_wikipedia_dyk.py` | Wikipedia "Did You Know" monthly archives 2015–now | CC BY-SA | 5–10k | needs Gemini |
| `scrape_wikipedia_onthisday.py` | Wikimedia REST "On this day" — all 366 days | CC BY-SA | ~5k | ✅ |
| `scrape_reddit_til.py` | r/todayilearned top posts (via pullpush.io) | user content | 10–20k | needs Gemini |
| `scrape_nhs.py` | NHS conditions A-Z + sexual health + pregnancy | Open Gov Licence v3 | ~1k | ✅ |
| `scrape_medlineplus.py` | NIH MedlinePlus health topics XML dump | US public domain | ~1k+ | ✅ |
| `scrape_nasa_apod.py` | NASA Astronomy Picture of the Day 1995→now | US public domain | ~10k | ✅ |
| `scrape_jeopardy.py` | jwolle1 Jeopardy clue dataset (~538k clues) | public dataset | ~300k usable | as clue→fact |

## Setup

```bash
cd ~/Desktop/scrollwise
python3 -m venv venv
source venv/bin/activate
pip install -r generator/requirements.txt
```

## Run order

Scrapers are independent. Open 2-3 terminals to parallelize.

```bash
# fast (minutes), no enrichment needed
python generator/scrape_wikipedia_topics.py
python generator/scrape_wikipedia_onthisday.py
python generator/scrape_medlineplus.py
python generator/scrape_jeopardy.py

# slower (hours), no enrichment needed
python generator/scrape_nhs.py            # ~30-60 min
python generator/scrape_nasa_apod.py      # ~1-2 hr

# slowest (hours), need Gemini detail later
python generator/scrape_wikipedia_dyk.py  # ~15 min
python generator/scrape_reddit_til.py     # ~1-2 hr

# combine + dedupe + categorize
python generator/merge_and_categorize.py

# (optional) fill missing detail paragraphs via Gemini for facts lacking them
python generator/enrich_with_gemini.py
```

## Output

- `data/raw/*.json` — one file per scraper
- `data/facts.json` — combined, deduped, categorized output the app reads

## Categories

The merge step routes facts to one of these app categories by keyword (or honors `category` set by the scraper itself): Mental Health, Human Body, This Day in History, Science, Space, History, Tech, AI, Psychology, Money, Health, Nature, Pop Culture, Sports, Food, Geography, Language, Misc.
