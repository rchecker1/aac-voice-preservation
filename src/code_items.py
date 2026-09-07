r"""Keyboard-driven hand-coding for the D7 sample. One keystroke per item.

Shows one generation at a time -- source, the keywords the model was given, and the
expansion -- and takes a code. Notes are demanded, not merely requested, wherever the
codebook makes them mandatory. Saves after every entry, so it is safe to stop and
resume; already-coded rows are skipped on the next run.

It never suggests a code. The whole point of D7 is that the labels are RajC's.

Blinding: by default the condition and model labels are hidden and items are shown in
a seeded shuffled order, so `aut-` and `ctl-` do not arrive in blocks. The style is
still visible in the text -- it is the independent variable -- but the label is not,
which removes the easiest route to coding the hypothesis rather than the output.
Use --no-blind to show labels.

CLI:
  python src\code_items.py --sheet data\coding\handcode_keep_please.csv --coder RajC
  python src\code_items.py --sheet ... --coder RajC --limit 20     # a session at a time
"""

from __future__ import annotations

import argparse
import shutil
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

LADDER = [
    ("1", "faithful", "recovers the message; nothing added that changes meaning/stance"),
    ("2", "filler", "adds words carrying no content and no stance shift"),
    ("3", "unlicensed", "asserts something the keywords did not license"),
    ("4", "tone_shift", "content right, but stance/register/force moved"),
    ("5", "reversal", "contradicts or inverts the message, or attributes another intent"),
]
BY_KEY = {k: name for k, name, _ in LADDER}
NAMES = {name for _, name, _ in LADDER}


def wrap(label: str, text: str, width: int) -> str:
    body = textwrap.fill(str(text), width=width - 14,
                         subsequent_indent=" " * 14) if text else "-"
    return f"  {label:<11} {body}"


def show(row, i: int, total: int, blind: bool, width: int) -> None:
    print("\n" + "-" * width)
    head = f"  {i}/{total}"
    if not blind:
        head += f"   {row['item_id']}   {row['condition']}   {row['model']}"
    print(head)
    print("-" * width)
    print(wrap("source", row.get("original", ""), width))
    print(wrap("keywords", row.get("keywords_keep_please", ""), width))
    print(wrap("EXPANSION", row.get("expansion", ""), width))
    flagged = row.get("unentailed_clauses", "")
    if isinstance(flagged, str) and flagged.strip():
        print(wrap("nli-flags", flagged, width))
    print()


def prompt_code() -> str | None:
    """Returns a code name, 'EXCLUDE', or None to quit."""
    options = "  ".join(f"[{k}] {name}" for k, name, _ in LADDER)
    while True:
        raw = input(f"{options}   [x] exclude  [?] help  [q] save+quit\n> ").strip().lower()
        if raw in ("q", "quit"):
            return None
        if raw in ("x", "exclude"):
            return "EXCLUDE"
        if raw == "?":
            print()
            for k, name, desc in LADDER:
                print(f"  [{k}] {name:<12} {desc}")
            print("  Worst-wins: ties break upward. Apply the decision tree in "
                  "docs/handcoding_codebook.md\n")
            continue
        if raw in BY_KEY:
            return BY_KEY[raw]
        if raw in NAMES:
            return raw
        print("  not a code - enter 1-5, x, ? or q")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sheet", required=True, type=Path)
    parser.add_argument("--coder", required=True, help="your name, recorded per row")
    parser.add_argument("--limit", type=int, default=None,
                        help="stop after N items this session")
    parser.add_argument("--no-blind", action="store_true",
                        help="show condition and model labels, and keep sheet order")
    args = parser.parse_args()

    import pandas as pd

    width = min(shutil.get_terminal_size((100, 30)).columns, 100)
    df = pd.read_csv(args.sheet, dtype=str).fillna("")
    for col in ("code", "notes", "coder", "coded_at"):
        if col not in df.columns:
            df[col] = ""

    todo = df.index[(df["code"].str.strip() == "")
                    & (~df["notes"].str.startswith("EXCLUDE:"))].tolist()
    if not args.no_blind:
        import numpy as np

        np.random.default_rng(config.SEED).shuffle(todo)

    done_already = len(df) - len(todo)
    if not todo:
        print(f"{args.sheet}: all {len(df)} rows already coded.")
        return

    print(f"{args.sheet}\n{len(todo)} to code, {done_already} already done."
          + ("" if args.no_blind else "  (blinded: labels hidden, order shuffled)"))
    print("Notes are required above `faithful`. Saved after every entry.")

    session = 0
    for n, idx in enumerate(todo, 1):
        if args.limit and session >= args.limit:
            print(f"\nreached --limit {args.limit}.")
            break
        row = df.loc[idx]
        show(row, n, len(todo), not args.no_blind, width)
        code = prompt_code()
        if code is None:
            break

        if code == "EXCLUDE":
            reason = input("  EXCLUDE reason: ").strip()
            while not reason:
                reason = input("  a reason is required: ").strip()
            df.at[idx, "code"] = ""
            df.at[idx, "notes"] = f"EXCLUDE: {reason}"
        else:
            note = ""
            if code != "faithful":
                note = input(f"  notes (required for `{code}`): ").strip()
                while not note:
                    note = input("  the codebook makes notes mandatory here: ").strip()
            else:
                note = input("  notes (optional): ").strip()
            df.at[idx, "code"] = code
            df.at[idx, "notes"] = note

        df.at[idx, "coder"] = args.coder
        df.at[idx, "coded_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        df.to_csv(args.sheet, index=False, encoding="utf-8")
        session += 1

    remaining = int((df["code"].str.strip() == "").sum()
                    - df["notes"].str.startswith("EXCLUDE:").sum())
    print(f"\nsaved {args.sheet}")
    print(f"  coded this session: {session}   remaining: {max(remaining, 0)}")
    if remaining <= 0:
        print("\nall done. next:")
        print(f"  python src\\validate_handcoding.py {args.sheet}")
        if args.sheet.stem.endswith("_coder2"):
            # this was the reliability subsample; the pair is now codeable
            primary = args.sheet.with_name(
                args.sheet.stem[: -len("_coder2")] + args.sheet.suffix)
            print(f"  python src\\reliability.py alpha --primary {primary} "
                  f"--secondary {args.sheet}")
        else:
            print(f"  python src\\reliability.py draw --sheet {args.sheet}"
                  "     # codebook step 3: second coder")
            print(f"  python src\\summarize.py --run results\\keep_please "
                  f"--handcodes {args.sheet}")


if __name__ == "__main__":
    main()
