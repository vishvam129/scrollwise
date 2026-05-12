"""Pull Wikipedia article intros across curated topic lists.

This is the highest-quality source: each article intro is already a well-written
2-4 sentence explanation that maps cleanly to our title + detail schema.
No API key, no enrichment step required for these facts.

Uses MediaWiki Action API:
  https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1

Output: data/raw/wikipedia_topics.json
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests
from tqdm import tqdm

API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "scrollwise-scraper/0.1 (personal project)"}
OUT = Path(__file__).resolve().parent.parent / "data" / "raw" / "wikipedia_topics.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
BATCH = 10  # titles per API call (was 20 -> hit 429s)
SLEEP = 1.5
MAX_RETRIES = 4


# Curated topic lists per category. Each entry is a Wikipedia article title.
TOPICS: dict[str, list[str]] = {
    "Human Body": [
        # core anatomy / systems
        "Human body",
        "Human anatomy",
        "Circulatory system",
        "Nervous system",
        "Digestive system",
        "Endocrine system",
        "Immune system",
        "Reproductive system",
        "Female reproductive system",
        "Male reproductive system",
        "Lymphatic system",
        "Skeletal system",
        "Muscular system",
        # development & life stages
        "Puberty",
        "Adolescence",
        "Menarche",
        "Spermarche",
        "Adrenarche",
        "Tanner scale",
        "Growth spurt",
        "Aging",
        "Menopause",
        "Perimenopause",
        "Andropause",
        # reproductive anatomy
        "Clitoris",
        "Vulva",
        "Vagina",
        "Uterus",
        "Cervix",
        "Fallopian tube",
        "Ovary",
        "Penis",
        "Glans penis",
        "Foreskin",
        "Circumcision",
        "Testicle",
        "Scrotum",
        "Epididymis",
        "Prostate",
        "Seminal vesicle",
        "G-spot",
        "Hymen",
        # cycle & fertility
        "Menstrual cycle",
        "Menstruation",
        "Ovulation",
        "Follicular phase",
        "Luteal phase",
        "Premenstrual syndrome",
        "Premenstrual dysphoric disorder",
        "Dysmenorrhea",
        "Endometriosis",
        "Polycystic ovary syndrome",
        "Fertility",
        "Infertility",
        "Sperm",
        "Spermatozoon",
        "Spermatogenesis",
        "Oogenesis",
        "Egg cell",
        "Fertilisation",
        "Implantation (human embryo)",
        # pregnancy
        "Pregnancy",
        "Conception",
        "Embryo",
        "Fetus",
        "Gestational age",
        "Prenatal development",
        "Miscarriage",
        "Stillbirth",
        "Ectopic pregnancy",
        "Childbirth",
        "Postpartum period",
        "Lactation",
        "Breastfeeding",
        "Postpartum depression",
        # contraception
        "Birth control",
        "Combined oral contraceptive pill",
        "Progestogen-only pill",
        "Intrauterine device",
        "Hormonal IUD",
        "Copper IUD",
        "Contraceptive implant",
        "Contraceptive patch",
        "Contraceptive injection",
        "Vaginal ring",
        "Diaphragm (contraceptive)",
        "Cervical cap",
        "Condom",
        "Female condom",
        "Spermicide",
        "Tubal ligation",
        "Vasectomy",
        "Coitus interruptus",
        "Fertility awareness",
        "Emergency contraception",
        "Levonorgestrel",
        "Ulipristal acetate",
        # STIs / STDs
        "Sexually transmitted infection",
        "HIV/AIDS",
        "Human papillomavirus infection",
        "HPV vaccine",
        "Chlamydia",
        "Gonorrhea",
        "Syphilis",
        "Genital herpes",
        "Trichomoniasis",
        "Pubic lice",
        "Scabies",
        "Hepatitis B",
        "Hepatitis C",
        "Pelvic inflammatory disease",
        "Bacterial vaginosis",
        "Candidiasis",
        # behavior / health
        "Human sexual activity",
        "Human sexuality",
        "Sexual intercourse",
        "Sexual arousal",
        "Orgasm",
        "Refractory period (sex)",
        "Masturbation",
        "Erection",
        "Ejaculation",
        "Pre-ejaculate",
        "Erectile dysfunction",
        "Premature ejaculation",
        "Vaginismus",
        "Dyspareunia",
        "Anorgasmia",
        "Libido",
        "Sexual response cycle",
        # consent & relationships
        "Consent (criminal law)",
        "Sexual consent",
        "Bodily integrity",
        "Sex education",
        "Comprehensive sex education",
        "Abstinence-only sex education",
        # identity & orientation
        "Sexual orientation",
        "Gender identity",
        "Heterosexuality",
        "Homosexuality",
        "Bisexuality",
        "Asexuality",
        "Pansexuality",
        "Transgender",
        "Non-binary gender",
        "Intersex",
        "Cisgender",
        # hormones & endocrinology
        "Hormone",
        "Estrogen",
        "Testosterone",
        "Progesterone",
        "Luteinizing hormone",
        "Follicle-stimulating hormone",
        "Gonadotropin-releasing hormone",
        "Oxytocin",
        "Prolactin",
        "Dopamine",
        # screening & care
        "Pap test",
        "Cervical screening",
        "HPV test",
        "Mammography",
        "Pelvic examination",
        "Testicular self-examination",
    ],
    "Science": [
        "Physics",
        "Chemistry",
        "Biology",
        "DNA",
        "Gene",
        "Evolution",
        "Natural selection",
        "Cell (biology)",
        "Mitochondrion",
        "Photosynthesis",
        "Quantum mechanics",
        "Theory of relativity",
        "Speed of light",
        "Periodic table",
        "Atom",
        "Higgs boson",
        "Entropy",
        "Thermodynamics",
        "Big Bang",
        "Black hole",
        "Schrödinger's cat",
        "Heisenberg uncertainty principle",
    ],
    "Space": [
        "Solar System",
        "Sun",
        "Moon",
        "Mercury (planet)",
        "Venus",
        "Mars",
        "Jupiter",
        "Saturn",
        "Uranus",
        "Neptune",
        "Pluto",
        "Milky Way",
        "Galaxy",
        "Universe",
        "Big Bang",
        "Black hole",
        "Neutron star",
        "Supernova",
        "Asteroid",
        "Comet",
        "International Space Station",
        "Voyager 1",
        "Hubble Space Telescope",
        "James Webb Space Telescope",
        "Dark matter",
        "Dark energy",
    ],
    "History": [
        "Ancient Egypt",
        "Ancient Rome",
        "Roman Empire",
        "Ancient Greece",
        "Mesopotamia",
        "Indus Valley civilisation",
        "Han dynasty",
        "Byzantine Empire",
        "Islamic Golden Age",
        "Renaissance",
        "Industrial Revolution",
        "French Revolution",
        "American Revolution",
        "World War I",
        "World War II",
        "Cold War",
        "Space Race",
        "Genghis Khan",
        "Cleopatra",
        "Napoleon",
        "Alexander the Great",
    ],
    "Tech": [
        "Computer",
        "Internet",
        "World Wide Web",
        "Transistor",
        "Integrated circuit",
        "Personal computer",
        "Smartphone",
        "Operating system",
        "Linux",
        "Unix",
        "Open-source software",
        "Cryptography",
        "Public-key cryptography",
        "Blockchain",
        "Bitcoin",
        "Quantum computing",
        "Cloud computing",
        "Semiconductor device fabrication",
    ],
    "AI": [
        "Artificial intelligence",
        "Machine learning",
        "Deep learning",
        "Neural network",
        "Transformer (deep learning architecture)",
        "Large language model",
        "GPT-4",
        "Reinforcement learning",
        "Computer vision",
        "Natural language processing",
        "Alan Turing",
        "Turing test",
        "Symbolic artificial intelligence",
        "AI alignment",
        "AI safety",
    ],
    "Psychology": [
        "Psychology",
        "Memory",
        "Long-term memory",
        "Working memory",
        "Sleep",
        "REM sleep",
        "Dream",
        "Lucid dream",
        "Cognitive bias",
        "Confirmation bias",
        "Dunning–Kruger effect",
        "Placebo",
        "Stockholm syndrome",
        "Imposter syndrome",
        "Depression (mood)",
        "Anxiety",
        "Big Five personality traits",
        "Attachment theory",
        "Maslow's hierarchy of needs",
    ],
    "Money": [
        "Money",
        "Currency",
        "Banknote",
        "Inflation",
        "Stock market",
        "Compound interest",
        "Federal Reserve",
        "Cryptocurrency",
        "Gold standard",
        "Great Depression",
        "2008 financial crisis",
        "Hyperinflation",
        "Bond (finance)",
        "Index fund",
        "Warren Buffett",
    ],
    "Health": [
        "Vaccine",
        "Antibiotic",
        "Antibiotic resistance",
        "Cancer",
        "Heart disease",
        "Stroke",
        "Diabetes",
        "Obesity",
        "Vitamin D",
        "Sleep hygiene",
        "Mediterranean diet",
        "Placebo",
        "Mental health",
        "Major depressive disorder",
        "Anxiety disorder",
        "ADHD",
        "Autism",
    ],
    "Nature": [
        "Octopus",
        "Cephalopod intelligence",
        "Honey bee",
        "Ant",
        "Coral reef",
        "Amazon rainforest",
        "Great Barrier Reef",
        "Tardigrade",
        "Mantis shrimp",
        "Axolotl",
        "Blue whale",
        "Sequoia",
        "Mycorrhiza",
        "Fungus",
        "Slime mold",
    ],
    "Geography": [
        "Mount Everest",
        "Mariana Trench",
        "Sahara",
        "Antarctica",
        "Amazon River",
        "Nile",
        "Pacific Ocean",
        "Atlantic Ocean",
        "Dead Sea",
        "Lake Baikal",
        "Iceland",
        "Hawaii",
    ],
    "Language": [
        "Language",
        "Indo-European languages",
        "Mandarin Chinese",
        "English language",
        "Latin",
        "Sanskrit",
        "Sign language",
        "Writing system",
        "Alphabet",
        "Esperanto",
        "Linguistics",
    ],
}


def fetch_intros(titles: list[str]) -> dict[str, str]:
    """Return {title: intro_text} for a batch of titles, with retry/backoff on 429."""
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "redirects": 1,
        "titles": "|".join(titles),
    }
    delay = 2.0
    for attempt in range(MAX_RETRIES):
        r = requests.get(API, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 429:
            time.sleep(delay)
            delay *= 2
            continue
        r.raise_for_status()
        data = r.json()
        break
    else:
        raise RuntimeError("Wikipedia API kept returning 429 after retries")
    out: dict[str, str] = {}
    for page in data.get("query", {}).get("pages", {}).values():
        if "missing" in page:
            continue
        title = page.get("title")
        extract = (page.get("extract") or "").strip()
        if title and extract:
            out[title] = extract
    return out


def split_title_detail(text: str) -> tuple[str, str]:
    """Use the first full sentence as the title, the rest as the detail."""
    text = re.sub(r"\s+", " ", text).strip()
    m = re.search(r"(?<=[.!?])\s+(?=[A-Z(])", text)
    if not m:
        return text, ""
    cut = m.start()
    title = text[:cut].strip()
    detail = text[cut:].strip()
    # cap detail so we don't dump a huge paragraph
    if len(detail) > 700:
        # try to end on a sentence boundary
        m2 = list(re.finditer(r"[.!?]\s+", detail[:700]))
        if m2:
            detail = detail[: m2[-1].end()].strip()
        else:
            detail = detail[:700].rsplit(" ", 1)[0] + "…"
    return title, detail


def main() -> None:
    # Resume: load anything we already have so reruns skip completed titles.
    facts: list[dict] = []
    if OUT.exists():
        try:
            facts = json.loads(OUT.read_text())
            print(f"Resuming with {len(facts)} previously saved facts")
        except Exception:
            facts = []
    seen: set[str] = {f["title"].lower() for f in facts if f.get("title")}
    have_urls: set[str] = {f.get("url") for f in facts if f.get("url")}

    total = sum(len(v) for v in TOPICS.values())
    pbar = tqdm(total=total, desc="wikipedia topics")

    for category, titles in TOPICS.items():
        for i in range(0, len(titles), BATCH):
            chunk = titles[i : i + BATCH]
            # skip titles whose Wikipedia URL is already in our saved facts
            pending = [
                t
                for t in chunk
                if f"https://en.wikipedia.org/wiki/{t.replace(' ', '_')}"
                not in have_urls
            ]
            if not pending:
                pbar.update(len(chunk))
                continue
            try:
                intros = fetch_intros(pending)
            except Exception as e:
                print(f"\n  ! batch failed: {e}")
                intros = {}
            for original in chunk:
                pbar.update(1)
                # API may have normalized via redirects; try exact match first,
                # otherwise just take any unmatched extract
                text = intros.get(original)
                if not text:
                    continue
                title, detail = split_title_detail(text)
                if not title or len(title) < 15:
                    continue
                key = title.lower()
                if key in seen:
                    continue
                seen.add(key)
                facts.append(
                    {
                        "id": f"wt_{category.lower().replace(' ', '_')}_{len(facts)}",
                        "source": "wikipedia_topic",
                        "category": category,
                        "title": title,
                        "detail": detail,
                        "url": f"https://en.wikipedia.org/wiki/{original.replace(' ', '_')}",
                    }
                )
            time.sleep(SLEEP)
    pbar.close()

    OUT.write_text(json.dumps(facts, ensure_ascii=False, indent=2))
    print(f"\nSaved {len(facts)} Wikipedia topic facts -> {OUT}")

    counts: dict[str, int] = {}
    for f in facts:
        counts[f["category"]] = counts.get(f["category"], 0) + 1
    for c, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {c:<14} {n}")


if __name__ == "__main__":
    main()
