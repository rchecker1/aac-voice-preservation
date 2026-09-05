r"""Validate the human-written style suites: schema, length stats, tag counts.

READ-ONLY. This script never edits, rewrites, or suggests replacement text for any
suite item -- all items are RajC's. Malformed items are reported by id so RajC can
fix them by hand.

Checks (ERROR = must fix, WARN = look at it):
- ERROR: unreadable JSON, missing/empty required field, wrong type, duplicate id,
  duplicate text within a set, `set` not matching the filename.
- WARN:  word count outside the 5-20 range in data/README.md, unknown style tag,
  tag with no citation in data/suites/feature_sources.md, id prefix not matching
  the set, item that compress.py would exclude (< 2 keywords).

Stats printed per file: n items, word-count mean/median/min/max, tag counts,
topic counts, keyword-count histogram.

CLI:
  python src\validate_suites.py                      # all *.jsonl in data\suites
  python src\validate_suites.py --in data\suites\autistic_style.jsonl
  python src\validate_suites.py --no-compress-preview # skip the spaCy pass
Exit code 1 if any ERROR was found.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

REQUIRED_FIELDS = {
    "id": str,
    "set": str,
    "style_tags": list,
    "text": str,
    "topic": str,
}
OPTIONAL_FIELDS = {"source_note": str}

# Candidate tags from data/README.md. Unknown tags are a WARN, not an ERROR: RajC may
# add tags, they just need a citation in feature_sources.md first.
KNOWN_TAGS = {"direct", "literal", "info_dense", "scripted", "low_hedging"}
ID_PREFIXES = {"autistic_style": "aut", "control_style": "ctl"}

MIN_WORDS, MAX_WORDS = 5, 20
FEATURE_SOURCES = config.DATA_SUITES / "feature_sources.md"


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def _load(path: Path, rep: Report) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                rep.error(f"line {lineno}: invalid JSON ({exc})")
                continue
            if not isinstance(rec, dict):
                rep.error(f"line {lineno}: expected a JSON object")
                continue
            rec["_lineno"] = lineno
            records.append(rec)
    return records


def _feature_sources_text() -> str | None:
    """Lowercased feature_sources.md, or None if RajC has not written it yet."""
    if not FEATURE_SOURCES.exists():
        return None
    return FEATURE_SOURCES.read_text(encoding="utf-8").lower()


def check_file(path: Path, compress_preview: bool) -> Report:
    rep = Report()
    records = _load(path, rep)
    expected_set = path.stem
    cited = _feature_sources_text()

    seen_ids: dict[str, int] = {}
    seen_texts: dict[str, str] = {}
    word_counts: list[int] = []
    tag_counts: Counter = Counter()
    topic_counts: Counter = Counter()
    kw_hist: Counter = Counter()
    would_exclude: list[str] = []
    uncited: Counter = Counter()

    compress_fn = None
    if compress_preview and records:
        from compress import MIN_KEYWORDS, compress  # local import: spaCy is slow

        compress_fn = compress

    for rec in records:
        lineno = rec.pop("_lineno")
        where = f"line {lineno}"
        rid = rec.get("id")
        if isinstance(rid, str) and rid:
            where = f"{rid} (line {lineno})"

        for field, typ in REQUIRED_FIELDS.items():
            if field not in rec:
                rep.error(f"{where}: missing required field {field!r}")
            elif not isinstance(rec[field], typ):
                rep.error(f"{where}: field {field!r} should be "
                          f"{typ.__name__}, got {type(rec[field]).__name__}")
            elif typ is str and not rec[field].strip():
                rep.error(f"{where}: field {field!r} is empty")
        for field, typ in OPTIONAL_FIELDS.items():
            if field in rec and not isinstance(rec[field], typ):
                rep.error(f"{where}: field {field!r} should be {typ.__name__}")
        for field in set(rec) - set(REQUIRED_FIELDS) - set(OPTIONAL_FIELDS):
            rep.warn(f"{where}: unexpected field {field!r}")

        if isinstance(rid, str) and rid:
            if rid in seen_ids:
                rep.error(f"{where}: duplicate id, first seen on line {seen_ids[rid]}")
            seen_ids[rid] = lineno
            prefix = ID_PREFIXES.get(expected_set)
            if prefix and not rid.startswith(prefix):
                rep.warn(f"{where}: id does not start with {prefix!r}")

        rset = rec.get("set")
        if isinstance(rset, str) and rset != expected_set:
            rep.error(f"{where}: set is {rset!r} but the file is {expected_set}.jsonl")

        text = rec.get("text")
        if isinstance(text, str) and text.strip():
            norm = " ".join(text.lower().split())
            if norm in seen_texts:
                rep.error(f"{where}: duplicate text, same as {seen_texts[norm]}")
            seen_texts[norm] = rid if isinstance(rid, str) else where
            n_words = len(text.split())
            word_counts.append(n_words)
            if not MIN_WORDS <= n_words <= MAX_WORDS:
                rep.warn(f"{where}: {n_words} words, outside the "
                         f"{MIN_WORDS}-{MAX_WORDS} range in data/README.md")
            if compress_fn is not None:
                kws = compress_fn(text, config.MAX_KEYWORDS)
                kw_hist[len(kws)] += 1
                if len(kws) < MIN_KEYWORDS:
                    would_exclude.append(f"{where} -> {kws}")

        tags = rec.get("style_tags")
        if isinstance(tags, list):
            for tag in tags:
                if not isinstance(tag, str):
                    rep.error(f"{where}: style_tags entries must be strings")
                    continue
                tag_counts[tag] += 1
                if tag not in KNOWN_TAGS:
                    rep.warn(f"{where}: unknown style tag {tag!r} "
                             f"(known: {', '.join(sorted(KNOWN_TAGS))})")
                if cited is not None and tag.lower() not in cited:
                    uncited[tag] += 1

        topic = rec.get("topic")
        if isinstance(topic, str) and topic.strip():
            topic_counts[topic] += 1

    if cited is None:
        rep.warn(f"{FEATURE_SOURCES.name} does not exist yet: "
                 "every style tag needs a citation there before use (data/README.md)")
    for tag, n in uncited.items():
        rep.warn(f"tag {tag!r} used {n}x but not mentioned in {FEATURE_SOURCES.name}")
    for item in would_exclude:
        rep.warn(f"compress.py would exclude this item (< 2 keywords): {item}")

    # --- report ---
    print(f"\n=== {path} ===")
    print(f"items: {len(records)}")
    if word_counts:
        print(f"words: mean {statistics.mean(word_counts):.1f}, "
              f"median {statistics.median(word_counts):.0f}, "
              f"min {min(word_counts)}, max {max(word_counts)}")
    if tag_counts:
        print("tags:  " + ", ".join(f"{t}:{n}" for t, n in tag_counts.most_common()))
    if topic_counts:
        print("topics:" + ", ".join(f" {t}:{n}" for t, n in topic_counts.most_common()))
    if kw_hist:
        print("keyword counts: "
              + ", ".join(f"{k}:{kw_hist[k]}" for k in sorted(kw_hist))
              + f"   (excluded: {len(would_exclude)})")

    for msg in rep.errors:
        print(f"  ERROR {msg}")
    for msg in rep.warnings:
        print(f"  WARN  {msg}")
    if not rep.errors and not rep.warnings:
        print("  clean")
    return rep


def pair_report(paths: list[Path]) -> None:
    """Manipulation check across the two suites: is each pair actually matched?

    Prints, per pair, the within-pair keyword overlap the model will actually see and
    the content-word-count gap. High overlap means both halves reach the model as the
    same input, which is what lets a fidelity difference be attributed to style rather
    than to content. Reports only -- nothing here edits an item.
    """
    import re as _re

    from compress import _is_content, _nlp, compress

    items: dict[str, dict[str, dict]] = {}
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            m = _re.search(r"(\d+)", rec.get("id") or "")
            if m and isinstance(rec.get("text"), str) and isinstance(rec.get("set"), str):
                items.setdefault(m.group(1), {})[rec["set"]] = rec

    complete = {k: v for k, v in items.items()
                if "autistic_style" in v and "control_style" in v}
    print(f"\n=== pair check ===\npairs with both halves: {len(complete)} "
          f"(of {len(items)} numbered ids)")
    orphans = sorted(set(items) - set(complete))
    if orphans:
        print(f"  UNPAIRED ids (excluded from every paired test): {', '.join(orphans[:20])}")
    if not complete:
        return

    overlaps, gaps, weak = [], [], []
    for pid in sorted(complete):
        aut, ctl = complete[pid]["autistic_style"], complete[pid]["control_style"]
        ka, kc = set(compress(aut["text"])), set(compress(ctl["text"]))
        jac = len(ka & kc) / len(ka | kc) if (ka | kc) else 0.0
        ca = sum(1 for t in _nlp()(aut["text"]) if _is_content(t))
        cc = sum(1 for t in _nlp()(ctl["text"]) if _is_content(t))
        overlaps.append(jac)
        gaps.append(abs(ca - cc))
        if jac < 0.5 or abs(ca - cc) > 2:
            weak.append(f"{pid}: overlap {jac:.2f}, content-word gap {abs(ca - cc)}"
                        f"  aut={sorted(ka)}  ctl={sorted(kc)}")

    print(f"keyword overlap (Jaccard): mean {statistics.mean(overlaps):.2f}, "
          f"median {statistics.median(overlaps):.2f}, min {min(overlaps):.2f}")
    print(f"content-word gap: mean {statistics.mean(gaps):.1f}, max {max(gaps)}")
    if weak:
        print(f"\nloosely matched pairs ({len(weak)}) -- overlap < 0.50 or gap > 2.")
        print("Not errors. Loose matching means the two halves reach the model as")
        print("different inputs, so a fidelity difference could be content, not style:")
        for line in weak[:25]:
            print(f"  {line}")
        if len(weak) > 25:
            print(f"  ... and {len(weak) - 25} more")
    else:
        print("all pairs matched tightly (overlap >= 0.50, content-word gap <= 2)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="in_path", type=Path,
                        help="a single JSONL file (default: all in data/suites)")
    parser.add_argument("--no-compress-preview", action="store_true",
                        help="skip the spaCy pass that previews excluded items")
    args = parser.parse_args()

    if args.in_path:
        paths = [args.in_path]
    else:
        paths = sorted(config.DATA_SUITES.glob("*.jsonl"))
    if not paths:
        print(f"no suite files found in {config.DATA_SUITES} "
              "(they are RajC's to write -- see data/README.md)")
        raise SystemExit(0)

    n_err = n_warn = 0
    for path in paths:
        if not path.exists():
            print(f"{path}: not found")
            raise SystemExit(1)
        rep = check_file(path, compress_preview=not args.no_compress_preview)
        n_err += len(rep.errors)
        n_warn += len(rep.warnings)

    if len(paths) > 1 and not args.no_compress_preview:
        pair_report(paths)

    print(f"\n{len(paths)} file(s): {n_err} error(s), {n_warn} warning(s)")
    raise SystemExit(1 if n_err else 0)


if __name__ == "__main__":
    main()
