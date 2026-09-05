r"""Build the hand-coding sheet for a run, from that run's actual outputs.

Takes the stratified sample metrics.py already drew -- seeded, and balanced across
condition x model x NLI-flag so the flag-vs-code agreement analysis is meaningful --
and adds the context columns the codebook and validator expect.

Why this exists rather than regenerating the sheet from the suite files: the coder must
see the keywords the model was actually given. Keywords produced by any other
compressor will disagree with the pipeline (measured: 38/100 for one such sheet), and
the codebook says to code what the keywords licensed, so wrong keywords give wrong
codes. Everything here is copied out of results/, never recomputed.

One row = one generation (a specific item, model and sample), not one item, because
each item was expanded k times by each model and the code applies to an output.

CLI:
  python src\make_coding_sheet.py --run results\keep_please
  python src\make_coding_sheet.py --run results\keep_please --out data\coding\sheet.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", required=True, type=Path, help="results/<run_id>/")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    import pandas as pd

    run_id = args.run.name
    sheet = pd.read_csv(args.run / f"handcode_sample_{run_id}.csv")

    # suite metadata: topic and feature tags, keyed by item id
    meta = {}
    for path in sorted((Path("data") / "suites").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                meta[rec["id"]] = rec

    sheet["topic"] = sheet["item_id"].map(lambda i: meta.get(i, {}).get("topic", ""))
    sheet["features"] = sheet["item_id"].map(
        lambda i: ";".join(meta.get(i, {}).get("style_tags") or []))
    # names the codebook and validate_handcoding.py expect
    sheet = sheet.rename(columns={"source_text": "original",
                                  "keywords": "keywords_keep_please"})
    sheet["coder"] = ""
    sheet["coded_at"] = ""

    order = ["item_id", "condition", "topic", "features", "original",
             "keywords_keep_please", "model", "sample_idx", "expansion",
             "n_clauses", "n_unentailed", "unentailed_clauses",
             "code", "notes", "coder", "coded_at"]
    sheet = sheet[[c for c in order if c in sheet.columns]]

    out = args.out or (Path("data") / "coding" / f"handcode_{run_id}.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.to_csv(out, index=False, encoding="utf-8")

    print(f"wrote {out}  ({len(sheet)} rows)")
    print("  one row per generation; every column copied from "
          f"{args.run.as_posix()}")
    print("  composition: " + ", ".join(
        f"{k}={v}" for k, v in sheet.groupby(["condition", "model"])
        .size().items()))
    blank = int((sheet["expansion"].astype(str).str.strip() == "").sum())
    print(f"  rows with an empty expansion: {blank} (must be 0 to be codable)")


if __name__ == "__main__":
    main()
