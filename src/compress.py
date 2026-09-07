r"""Deterministic keyword compression: full utterance -> telegraphic AAC-style input.

Implements D1 (docs/design_decisions.md): keep content words by POS
(config.KEEP_POS = NOUN/PROPN/VERB/ADJ/NUM), drop auxiliaries and stopwords,
preserve order of appearance, cap at config.MAX_KEYWORDS.

Readings of D1 used here. Each is surfaced in the run report so RajC can confirm or
revise the decision -- none is silently "fixed":
- "drop stopwords/auxiliaries" targets function words, which the POS filter already
  removes (DET/ADP/PRON/PART/AUX are not in KEEP_POS). spaCy's stop list is therefore
  NOT applied to content words: it contains common verbs (go, get, call, give) and
  number words (three), and applying it excluded 39% of the AAC dev corpus for
  yielding < 2 keywords. Content words the old reading would have dropped are still
  counted in the run report as STOPWORD-DROPPED, for the Methods footnote.
- "keep numbers as digits" = NUM tokens keep their surface form ("3" stays "3");
  number words are not converted to digits (that would be a rewrite, not a filter).
- No de-duplication: a repeated keyword occupies a slot, since "order of appearance,
  cap N" says nothing about collapsing repeats. Reported as DUPLICATE.

compress() is pure: same input -> same output, no randomness.
Utterances yielding fewer than MIN_KEYWORDS (2) keywords are excluded and logged.

CLI:
  python src\compress.py --in data\suites\autistic_style.jsonl \
      --out results\compressed_autistic_style.jsonl
  python src\compress.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

SPACY_MODEL = "en_core_web_sm"
MIN_KEYWORDS = 2  # D1 edge case: fewer than this and the item is excluded

# D1b (RajC, 2026-09-05): politeness markers are kept regardless of POS tag. They are
# user-authored, so preserving them is what lets RQ3 tell an unlicensed politeness
# addition apart from a faithfully preserved one. spaCy tags "please" five different
# ways across the corpus (INTJ 261, NOUN 15, VERB 11, ADV 1, AUX 1 in sent_train_aac),
# so without this list the rule kept it only 26/289 times, at the tagger's whim.
ALWAYS_KEEP = {"please"}

# Alternative D1b reading, selected with --strip-register: politeness and hedge
# markers are register, not proposition, and are removed BEFORE the cap applies, so
# they never compete with content for the four slots. Consequence to state in Methods:
# matched pairs then compress to near-identical keyword sets, so the model receives
# one bottleneck and produces one expansion which is scored against two differently
# styled sources. Cost: RQ3 can no longer tell an authored politeness marker from an
# invented one, which is the argument that motivated the default mode.
POLITENESS = {"please", "sorry", "thanks", "thank"}

# D14 ablation, selected with --keep-negation: negation is carried by function words,
# which the D1 content-word rule deletes -- measured at 0/96 keyword sets retaining it
# on the keep_please run, and 75% of negated sources then hand-coded as `reversal`.
# This mode keeps negation tokens regardless of POS, before the cap, so the question
# "does the model restore polarity when the keywords actually carry it?" is separable
# from "does the compressor destroy polarity?". It is an ablation, not a D1 revision:
# the default rule is unchanged and both arms are reported.
NEGATION = {"not", "n't", "no", "never", "none", "neither", "nor", "cannot",
            "nothing", "nobody", "nowhere", "without"}
HEDGE_FILE = ROOT_HEDGES = Path(__file__).resolve().parent / "hedges.txt"


def load_register_terms() -> tuple[set[str], list[tuple[str, ...]]]:
    """Single-token and multi-token register terms from hedges.txt, plus politeness."""
    singles, phrases = set(POLITENESS), []
    if HEDGE_FILE.exists():
        for line in HEDGE_FILE.read_text(encoding="utf-8").splitlines():
            term = line.split("#", 1)[0].strip().lower()
            if not term:
                continue
            parts = tuple(term.split())
            (singles.add(parts[0]) if len(parts) == 1 else phrases.append(parts))
    return singles, sorted(phrases, key=len, reverse=True)  # longest match first


def _register_mask(doc, singles: set[str], phrases: list[tuple[str, ...]]) -> set[int]:
    """Indices of tokens covered by a register term (single word or phrase)."""
    words = [t.text.lower() for t in doc]
    masked = {i for i, w in enumerate(words) if w in singles}
    for phrase in phrases:
        n = len(phrase)
        for i in range(len(words) - n + 1):
            if tuple(words[i:i + n]) == phrase:
                masked.update(range(i, i + n))
    return masked

_NLP = None


def _nlp():
    """Load the spaCy pipeline once (deterministic, no randomness)."""
    global _NLP
    if _NLP is None:
        import spacy

        _NLP = spacy.load(SPACY_MODEL)
    return _NLP


def _is_content(token) -> bool:
    """POS half of D1: content word, not an auxiliary."""
    if token.is_space or token.is_punct:
        return False
    if token.pos_ == "AUX" or token.dep_ in ("aux", "auxpass"):
        return False
    return token.pos_ in config.KEEP_POS


def _is_negation(token) -> bool:
    """D14: negation by dependency label or surface form. Both, because spaCy tags
    contracted "n't" as dep_ == "neg" but standalone determiner "no" as det."""
    return token.dep_ == "neg" or token.text.lower().lstrip("’'") in NEGATION


def _keep(token) -> bool:
    """Full D1 filter.

    D1 refinement (RajC, 2026-09-05): the stopword clause applies only to non-content
    parts of speech, which KEEP_POS already excludes -- so KEEP_POS alone decides.
    spaCy's stop list is not applied to content words, because it contains common
    verbs (go, get, call, give) and number words (three), and dropping those excluded
    39% of the AAC dev corpus for yielding < 2 keywords.
    """
    if token.text.lower() in ALWAYS_KEEP:  # D1b
        return True
    return _is_content(token)


def compress(text: str, max_keywords: int = config.MAX_KEYWORDS,
             strip_register: bool = False, keep_negation: bool = False) -> list[str]:
    """Full utterance -> ordered list of at most max_keywords lowercased keywords.

    strip_register=False (default, D1b as decided): politeness markers are kept and
    count against the cap. strip_register=True: register terms are removed first.
    """
    doc = _nlp()(text)
    if not strip_register:
        return [t.text.lower() for t in doc
                if _keep(t) or (keep_negation and _is_negation(t))][:max_keywords]
    masked = _register_mask(doc, *load_register_terms())
    return [t.text.lower() for t in doc
            if (t.i not in masked and _is_content(t))
            or (keep_negation and _is_negation(t))][:max_keywords]


# --- diagnostics: surface the consequences of the D1 wording, never change it ---

def stopword_dropped_content(text: str) -> list[str]:
    """Content-POS tokens removed only because spaCy calls them stopwords."""
    return [t.text.lower() for t in _nlp()(text) if _is_content(t) and t.is_stop]


def duplicate_keywords(text: str, max_keywords: int = config.MAX_KEYWORDS) -> list[str]:
    """Keywords that repeat within the capped output (each repeat costs a slot)."""
    counts = Counter(compress(text, max_keywords))
    return sorted(k for k, n in counts.items() if n > 1)


# --- CLI ---

def _read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{lineno}: invalid JSON ({exc})")
    return records


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run_file(in_path: Path, out_path: Path, max_keywords: int,
             strip_register: bool = False, keep_negation: bool = False) -> dict:
    records = _read_jsonl(in_path)
    kept: list[dict] = []
    excluded: list[dict] = []
    stopword_drops: Counter = Counter()
    dup_items: list[str] = []
    length_hist: Counter = Counter()

    for rec in records:
        if "text" not in rec:
            raise SystemExit(f"{in_path}: record {rec.get('id', '?')} has no text field")
        text = rec["text"]
        keywords = compress(text, max_keywords, strip_register, keep_negation)
        stopword_drops.update(stopword_dropped_content(text))
        if duplicate_keywords(text, max_keywords):
            dup_items.append(str(rec.get("id", "?")))
        length_hist[len(keywords)] += 1

        out_rec = dict(rec)
        out_rec["keywords"] = keywords
        if len(keywords) < MIN_KEYWORDS:
            out_rec["excluded_reason"] = f"fewer than {MIN_KEYWORDS} keywords"
            excluded.append(out_rec)
        else:
            kept.append(out_rec)

    _write_jsonl(out_path, kept)
    excluded_path = out_path.with_suffix(out_path.suffix + ".excluded")
    if excluded:
        _write_jsonl(excluded_path, excluded)

    print(f"in:       {in_path}  ({len(records)} records)")
    print(f"kept:     {out_path}  ({len(kept)})")
    print(f"excluded: {len(excluded)}" + (f"  -> {excluded_path}" if excluded else ""))
    print("keyword-count histogram: "
          + ", ".join(f"{n}:{length_hist[n]}" for n in sorted(length_hist)))
    if excluded:
        print("  excluded ids: " + ", ".join(str(r.get("id", "?")) for r in excluded))

    print("\nDIAGNOSTICS (consequences of the D1 wording -- for RajC, not auto-applied)")
    if stopword_drops:
        top = ", ".join(f"{w}({n})" for w, n in stopword_drops.most_common(15))
        print(f"  STOPWORD-DROPPED content tokens "
              f"({sum(stopword_drops.values())} total): {top}")
    else:
        print("  STOPWORD-DROPPED content tokens: none")
    print(f"  DUPLICATE keyword slots in {len(dup_items)} item(s)"
          + (": " + ", ".join(dup_items[:15]) if dup_items else ""))

    return {
        "in_path": str(in_path),
        "out_path": str(out_path),
        "n_in": len(records),
        "n_kept": len(kept),
        "n_excluded": len(excluded),
        "excluded_ids": [str(r.get("id", "?")) for r in excluded],
        "keyword_count_histogram": {str(k): v for k, v in sorted(length_hist.items())},
        "stopword_dropped_content": dict(stopword_drops.most_common()),
        "duplicate_keyword_items": dup_items,
        "max_keywords": max_keywords,
        "min_keywords": MIN_KEYWORDS,
        "spacy_model": SPACY_MODEL,
        "strip_register": strip_register,
    }


# --- self-test ---
# Toy sentences written to document the compression rule for the Methods section.
# These are NOT suite items and never enter the experiment. RajC signs off on the
# expected outputs: they are the rule, written down.
SELFTEST_CASES = [
    # "would" is AUX and dropped; "please" is tagged INTJ/VERB by spaCy and survives,
    # so politeness markers can reach the model as keywords in either suite.
    ("I would like a cup of coffee please.", ["like", "cup", "coffee", "please"]),
    ("Can you turn the light off in the kitchen?", ["turn", "light", "kitchen"]),
    ("The train to Boston leaves at 8 tomorrow morning.",
     ["train", "boston", "leaves", "8"]),
    ("My laptop battery died again.", ["laptop", "battery", "died"]),
    ("I am tired and I want to sleep.", ["tired", "want", "sleep"]),
    # "three" is NUM and survives like the digit "8" above; "market" is cut by the
    # MAX_KEYWORDS=4 cap, not by the filter.
    ("She bought three red apples at the market yesterday.",
     ["bought", "three", "red", "apples"]),
    # D1b in tension with the cap: keeping "please" costs a slot, and here the slot it
    # costs is "hurts" -- the predicate. See the D1b note in docs/design_decisions.md.
    ("Please tell the nurse my leg hurts.", ["please", "tell", "nurse", "leg"]),
    ("It is raining.", ["raining"]),
    ("Okay.", []),
    ("The meeting has been moved to Thursday because Priya is sick.",
     ["meeting", "moved", "thursday", "priya"]),
]


def selftest() -> int:
    failures = 0
    for text, expected in SELFTEST_CASES:
        got = compress(text, config.MAX_KEYWORDS)
        ok = got == expected
        failures += 0 if ok else 1
        print(f"  {'ok  ' if ok else 'FAIL'} {text!r}\n         got={got}"
              + ("" if ok else f"\n         exp={expected}"))
    n = len(SELFTEST_CASES)
    print(f"\n{n - failures}/{n} toy sentences match "
          f"(MAX_KEYWORDS={config.MAX_KEYWORDS}, MIN_KEYWORDS={MIN_KEYWORDS}).")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="in_path", type=Path, help="input JSONL")
    parser.add_argument("--out", dest="out_path", type=Path, help="output JSONL")
    parser.add_argument("--max-keywords", type=int, default=config.MAX_KEYWORDS)
    parser.add_argument("--strip-register", action="store_true",
                        help="remove hedge/politeness terms before the cap (D1b alt)")
    parser.add_argument("--keep-negation", action="store_true",
                        help="keep negation tokens regardless of POS (D14 ablation)")
    parser.add_argument("--report", type=Path, help="write run stats as JSON")
    parser.add_argument("--selftest", action="store_true",
                        help="run the toy-sentence self-test and exit")
    args = parser.parse_args()

    if args.selftest:
        raise SystemExit(1 if selftest() else 0)
    if not args.in_path or not args.out_path:
        parser.error("--in and --out are required (or use --selftest)")

    stats = run_file(args.in_path, args.out_path, args.max_keywords,
                     args.strip_register, args.keep_negation)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(stats, indent=2), encoding="utf-8")
        print(f"\nreport: {args.report}")


if __name__ == "__main__":
    main()
