"""Merge all raw scraped sources, dedupe, categorize by keyword, save final facts.json.

Inputs:  data/raw/*.json
Output:  data/facts.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "facts.json"

CATEGORIES: dict[str, list[str]] = {
    "Mental Health": [
        "depression",
        "anxiety",
        "panic attack",
        "adhd",
        "autism",
        "bipolar",
        "ocd",
        "ptsd",
        "schizophrenia",
        "suicide",
        "therapy",
        "psychiatry",
        "psychiatric",
        "mental illness",
        "mental health",
        "eating disorder",
        "anorexia",
        "bulimia",
        "self-harm",
        "burnout",
    ],
    "Science": [
        "science",
        "physics",
        "chemistry",
        "biology",
        "atom",
        "molecule",
        "experiment",
        "scientist",
        "research",
        "evolution",
        "gene",
        "dna",
        "cell",
        "neuron",
        "quantum",
    ],
    "Space": [
        "space",
        "planet",
        "star",
        "galaxy",
        "nasa",
        "moon",
        "mars",
        "sun",
        "universe",
        "black hole",
        "astronaut",
        "rocket",
        "orbit",
        "comet",
        "asteroid",
        "solar",
    ],
    "History": [
        "history",
        "ancient",
        "war",
        "century",
        "empire",
        "king",
        "queen",
        "battle",
        "roman",
        "egypt",
        "medieval",
        "world war",
        "revolution",
        "dynasty",
    ],
    "Tech": [
        "computer",
        "internet",
        "software",
        "hardware",
        "google",
        "apple",
        "microsoft",
        "smartphone",
        "linux",
        "programmer",
        "code",
        "algorithm",
        "silicon",
        "chip",
        "robot",
    ],
    "AI": [
        "artificial intelligence",
        " ai ",
        "machine learning",
        "neural network",
        "llm",
        "gpt",
    ],
    "Psychology": [
        "brain",
        "mind",
        "psychology",
        "memory",
        "dream",
        "sleep",
        "emotion",
        "behavior",
        "cognitive",
        "anxiety",
        "happiness",
    ],
    "Money": [
        "money",
        "dollar",
        "economy",
        "bank",
        "stock",
        "wealth",
        "rich",
        "billionaire",
        "currency",
        "trade",
        "market",
        "inflation",
    ],
    "Health": [
        "health",
        "disease",
        "medicine",
        "doctor",
        "vaccine",
        "virus",
        "blood",
        "heart",
        "cancer",
        "drug",
        "nutrition",
    ],
    "Nature": [
        "animal",
        "tree",
        "ocean",
        "forest",
        "river",
        "mountain",
        "bird",
        "fish",
        "insect",
        "species",
        "plant",
        "weather",
        "climate",
    ],
    "Pop Culture": [
        "movie",
        "film",
        "music",
        "song",
        "band",
        "actor",
        "actress",
        "tv",
        "show",
        "celebrity",
        "album",
    ],
    "Sports": [
        "football",
        "soccer",
        "basketball",
        "olympic",
        "athlete",
        "tennis",
        "cricket",
    ],
    "Food": [
        "food",
        "cook",
        "recipe",
        "fruit",
        "vegetable",
        "spice",
        "chocolate",
        "coffee",
        "tea",
    ],
    "Geography": [
        "country",
        "city",
        "capital",
        "continent",
        "island",
        "desert",
        "lake",
    ],
    "Language": ["language", "word", "english", "letter", "alphabet", "dictionary"],
    "Human Body": [
        "puberty",
        "menstruation",
        "menstrual",
        "period",
        "ovulation",
        "ovary",
        "uterus",
        "vagina",
        "vulva",
        "clitoris",
        "cervix",
        "penis",
        "testicle",
        "testes",
        "sperm",
        "semen",
        "erection",
        "ejaculation",
        "orgasm",
        "fertility",
        "infertility",
        "contraception",
        "contraceptive",
        "condom",
        "iud",
        "birth control",
        "pregnancy",
        "pregnant",
        "conception",
        "embryo",
        "fetus",
        "miscarriage",
        "abortion",
        "menopause",
        "hormone",
        "estrogen",
        "testosterone",
        "libido",
        "sexual",
        "intercourse",
        "consent",
        "sti ",
        "stds",
        "std ",
        "hiv",
        "aids",
        "hpv",
        "chlamydia",
        "gonorrhea",
        "herpes",
        "syphilis",
        "reproduction",
        "reproductive",
    ],
}

DEFAULT_CATEGORY = "Misc"

# basic cleanup helpers
URL_RE = re.compile(r"https?://\S+")
WHITESPACE_RE = re.compile(r"\s+")
LATIN_LETTER_RE = re.compile(r"[A-Za-z]")
ANY_LETTER_RE = re.compile(r"[^\W\d_]", flags=re.UNICODE)


def is_english(text: str, threshold: float = 0.9) -> bool:
    """Heuristic: keep facts whose letters are mostly Latin-alphabet.

    Tolerates accents/diacritics on otherwise-Latin words (café, María, μm)
    while rejecting passages dominated by Cyrillic, CJK, Arabic, etc.
    """
    if not text:
        return False
    total = len(ANY_LETTER_RE.findall(text))
    if total < 5:
        return False
    latin = len(LATIN_LETTER_RE.findall(text))
    return (latin / total) >= threshold


def categorize(text: str) -> str:
    t = " " + text.lower() + " "
    for cat, kws in CATEGORIES.items():
        for kw in kws:
            if kw in t:
                return cat
    return DEFAULT_CATEGORY


def clean(text: str) -> str:
    t = URL_RE.sub("", text)
    t = WHITESPACE_RE.sub(" ", t).strip()
    return t


def normalize_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())[:120]


def process_file(path: Path, seen: set[str], out: list[dict]) -> int:
    items = json.loads(path.read_text())
    kept = 0
    for it in items:
        # Wikipedia topics already split title/detail/category; everything
        # else gives us a single `text` field.
        if it.get("title"):
            title = clean(it["title"])
            detail = clean(it.get("detail", ""))
            category = it.get("category") or categorize(title)
        else:
            title = clean(it.get("text", ""))
            detail = ""
            category = categorize(title)
        if not title or len(title) < 25 or len(title) > 500:
            continue
        if not is_english(title + " " + detail):
            continue
        key = normalize_key(title)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "id": it.get("id"),
                "source": it.get("source"),
                "title": title,
                "detail": detail,
                "category": category,
                "url": it.get("url"),
            }
        )
        kept += 1
    return kept


def main() -> None:
    files = sorted(RAW.glob("*.json"))
    if not files:
        raise SystemExit(f"No raw files in {RAW}. Run the scrapers first.")

    all_facts: list[dict] = []
    seen: set[str] = set()

    for f in files:
        total = len(json.loads(f.read_text()))
        kept = process_file(f, seen, all_facts)
        print(f"  {f.name}: kept {kept}/{total}")

    # category breakdown
    counts: dict[str, int] = {}
    for f in all_facts:
        counts[f["category"]] = counts.get(f["category"], 0) + 1

    OUT.write_text(json.dumps(all_facts, ensure_ascii=False, indent=2))
    print(f"\nTotal unique facts: {len(all_facts)} -> {OUT}")
    print("By category:")
    for c, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {c:<14} {n}")


if __name__ == "__main__":
    main()
