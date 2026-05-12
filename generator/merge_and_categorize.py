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
        text = clean(it.get("text", ""))
        if not text or len(text) < 25 or len(text) > 500:
            continue
        key = normalize_key(text)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "id": it.get("id"),
                "source": it.get("source"),
                "title": text,
                "detail": "",
                "category": categorize(text),
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
