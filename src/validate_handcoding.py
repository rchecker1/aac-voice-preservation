#!/usr/bin/env python3
"""Validate a completed hand-coding sheet against codebook v1.0.

Usage: python3 validate_handcoding.py data/coding/handcode_sample_keep_please.csv
Exit 0 = clean. Exit 1 = errors. Run before any analysis.
"""
import csv, sys, collections

CODES = ["faithful", "filler", "unlicensed", "tone_shift", "reversal"]
SEVERITY = {c: i for i, c in enumerate(CODES)}
REQUIRED = ["item_id", "condition", "original", "keywords_keep_please",
            "model", "expansion", "code", "notes", "coder"]


def main(path):
    rows = list(csv.DictReader(open(path)))
    errs, excluded = [], 0

    missing = [c for c in REQUIRED if c not in rows[0]]
    if missing:
        print(f"FATAL: missing columns {missing}")
        return 1

    for i, r in enumerate(rows, start=2):
        rid = r["item_id"] or f"row{i}"
        code, notes = r["code"].strip(), r["notes"].strip()

        if notes.startswith("EXCLUDE:"):
            excluded += 1
            if code:
                errs.append(f"{rid}: excluded rows must leave `code` blank")
            continue

        if not code:
            errs.append(f"{rid}: `code` is blank (use EXCLUDE: in notes if uncodable)")
            continue
        if code not in SEVERITY:
            errs.append(f"{rid}: `code` = '{code}' is not in the ladder")
            continue
        # the contract: notes mandatory above faithful
        if SEVERITY[code] > 0 and not notes:
            errs.append(f"{rid}: code '{code}' requires a note")
        if not r["expansion"].strip():
            errs.append(f"{rid}: `expansion` is empty but a code was assigned")
        if not r["model"].strip():
            errs.append(f"{rid}: `model` is empty")
        if not r["coder"].strip():
            errs.append(f"{rid}: `coder` is empty")

    # Key on (item, model): the sample is stratified by model on purpose, so the same
    # item appearing once under each model is the design, not a duplicate. Two rows for
    # the same item AND model would mean one output was drawn twice.
    cells = [(r["item_id"], r.get("model", "")) for r in rows]
    for (dup, model), n in collections.Counter(cells).items():
        if n > 1:
            errs.append(f"{dup}: appears {n} times for model {model!r}")

    coded = [r for r in rows if r["code"].strip() in SEVERITY]
    print(f"{len(rows)} rows | {len(coded)} coded | {excluded} excluded | {len(errs)} errors\n")

    if coded:
        for cond in ("autistic", "control"):
            sub = [r for r in coded if r["condition"] == cond]
            if not sub:
                continue
            dist = collections.Counter(r["code"] for r in sub)
            mean = sum(SEVERITY[r["code"]] for r in sub) / len(sub)
            print(f"{cond:9s} n={len(sub):3d}  mean severity {mean:.2f}")
            for c in CODES:
                print(f"            {c:12s} {dist.get(c,0):3d}")
            print()
        print("Distribution above is descriptive only. Do not read a difference")
        print("off these means — run the pre-registered test (see decision 10).\n")

    if errs:
        print("ERRORS:")
        for e in errs:
            print("  -", e)
        return 1
    print("Clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else
                  "data/coding/handcode_sample_keep_please.csv"))
