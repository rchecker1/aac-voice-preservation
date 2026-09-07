r"""Inter-coder reliability for the D7 hand-coding pass (codebook v1.0, step 3).

Two subcommands, matching the two halves of the procedure:

  draw   -- pull a seeded subsample of the primary sheet and write a *blank* sheet
            for the second coder. Codes, notes and coder identity are stripped, so
            the second pass cannot be anchored by the first. This is the only
            reason the second coder is worth having.

  alpha  -- pair the two completed sheets on (item_id, model, sample_idx) and
            report Krippendorff's alpha on the ordinal ladder, plus the
            disagreements themselves, which are the part worth reading.

The ladder is ordinal, not nominal: `faithful` -> `reversal` is a worse miss than
`faithful` -> `filler`, and the ordinal metric charges accordingly. Nominal alpha is
printed alongside as a floor, since it ignores the ordering entirely.

The codebook sets the threshold: below 0.67, revise to v1.1 and recode everything.
That call is RajC's; this script only reports the number.

`--self-check` runs the implementation against pinned values on a standard
12-unit / 3-observer matrix with missing data. Those values were cross-checked
against the `krippendorff` PyPI package -- 600 randomised cases, 2-3 coders, both
metrics, agreement to 2e-16 -- and the check repeats that comparison live whenever
the package happens to be importable. It is not a runtime dependency. Run the
self-check once before trusting any alpha this file prints.

CLI:
  python src\reliability.py draw --sheet data\coding\handcode_keep_please.csv
  python src\reliability.py alpha --primary data\coding\handcode_keep_please.csv ^
                                  --secondary data\coding\handcode_keep_please_coder2.csv
  python src\reliability.py --self-check
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

# Ladder order is the ordinal scale. Must match docs/handcoding_codebook.md v1.0.
CODES = ["faithful", "filler", "unlicensed", "tone_shift", "reversal"]
RANK = {c: i for i, c in enumerate(CODES)}

THRESHOLD = 0.67  # codebook step 3
CODER_COLS = ["code", "notes", "coder", "coded_at"]


# --------------------------------------------------------------------------- alpha

def coincidence(units: list[list[int]], k: int) -> list[list[float]]:
    """Krippendorff's coincidence matrix over reliability units.

    Each unit contributes every ordered pair of its ratings, weighted 1/(m-1), so a
    unit rated by many coders does not outweigh one rated by two. Units with a single
    rating carry no information about agreement and are dropped by the caller.
    """
    o = [[0.0] * k for _ in range(k)]
    for vals in units:
        m = len(vals)
        if m < 2:
            continue
        w = 1.0 / (m - 1)
        for i in range(m):
            for j in range(m):
                if i != j:
                    o[vals[i]][vals[j]] += w
    return o


def _delta2(c: int, g: int, marg: list[float], metric: str) -> float:
    """Squared difference between two categories under the chosen metric."""
    if metric == "nominal":
        return 0.0 if c == g else 1.0
    # ordinal (Krippendorff): distance is the mass of ranks lying between them,
    # counting the endpoints half. Empty categories contribute nothing.
    lo, hi = (c, g) if c <= g else (g, c)
    d = sum(marg[lo:hi + 1]) - (marg[lo] + marg[hi]) / 2.0
    return d * d


def krippendorff(units: list[list[int]], k: int, metric: str = "ordinal") -> float | None:
    """Alpha over pre-ranked units. None when alpha is undefined (see below)."""
    o = coincidence(units, k)
    marg = [sum(row) for row in o]
    n = sum(marg)
    if n < 2:
        return None

    do = sum(o[c][g] * _delta2(c, g, marg, metric)
             for c in range(k) for g in range(k)) / n
    de = sum(marg[c] * marg[g] * _delta2(c, g, marg, metric)
             for c in range(k) for g in range(k)) / (n * (n - 1))
    if de == 0:
        return None  # every rating identical: no variance to explain, alpha undefined
    return 1.0 - do / de


def bootstrap_ci(units: list[list[int]], k: int, metric: str, seed: int,
                 reps: int = 2000, level: float = 0.95) -> tuple[float, float] | None:
    """Percentile CI by resampling *units* with replacement.

    Not Krippendorff's own interval procedure, which resamples within the
    coincidence matrix; this is the ordinary nonparametric bootstrap over coding
    units and is reported as such. With ~20 units it is wide, which is honest.
    """
    rng = random.Random(seed)
    n = len(units)
    if n < 2:
        return None
    draws = []
    for _ in range(reps):
        sample = [units[rng.randrange(n)] for _ in range(n)]
        a = krippendorff(sample, k, metric)
        if a is not None:
            draws.append(a)
    if len(draws) < reps // 2:
        return None  # too many degenerate resamples for the interval to mean anything
    draws.sort()
    tail = (1.0 - level) / 2.0
    return draws[int(tail * len(draws))], draws[min(int((1 - tail) * len(draws)),
                                                   len(draws) - 1)]


# ---------------------------------------------------------------------------- io

def read_sheet(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def unit_key(row: dict) -> tuple:
    """One coding unit = one generation, not one item: each item was expanded k
    times per model and the code applies to an output."""
    return (row.get("item_id", "").strip(),
            row.get("model", "").strip(),
            row.get("sample_idx", "").strip())


def code_of(row: dict) -> str | None:
    """The assigned code, or None for blank/excluded/unrecognised rows."""
    code = (row.get("code") or "").strip()
    return code if code in RANK else None


# -------------------------------------------------------------------------- draw

def cmd_draw(args: argparse.Namespace) -> int:
    rows = read_sheet(args.sheet)
    if not rows:
        print(f"FATAL: {args.sheet} is empty")
        return 1

    n = args.n if args.n else max(2, round(args.frac * len(rows)))
    if n > len(rows):
        print(f"FATAL: asked for {n} rows, sheet has {len(rows)}")
        return 1

    rng = random.Random(args.seed)
    if args.stratify:
        # equal-ish draw per condition x model, so the reliability sample cannot come
        # back all-autistic by chance. A deviation from the codebook's plain "randomly
        # drawn" -- off by default for that reason.
        strata: dict[tuple, list[int]] = {}
        for i, r in enumerate(rows):
            strata.setdefault((r.get("condition", ""), r.get("model", "")), []).append(i)
        picked: list[int] = []
        for j, (_, idxs) in enumerate(sorted(strata.items())):
            take = n // len(strata) + (1 if j < n % len(strata) else 0)
            picked += rng.sample(idxs, min(take, len(idxs)))
        picked.sort()
    else:
        picked = sorted(rng.sample(range(len(rows)), n))

    out = args.out or args.sheet.with_name(args.sheet.stem + "_coder2.csv")
    if out.exists() and not args.force:
        print(f"FATAL: {out} exists. Re-drawing would discard the second coder's work.")
        print("       Pass --force only if you are certain it is empty.")
        return 1

    blanked = []
    for i in picked:
        row = dict(rows[i])
        for col in CODER_COLS:          # the whole point: coder 2 sees no codes
            row[col] = ""
        blanked.append(row)

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(blanked)

    already = sum(1 for i in picked if code_of(rows[i]) is not None)
    print(f"wrote {out}  ({len(blanked)} rows, {len(blanked)/len(rows):.0%} of the sheet)")
    print(f"  seed {args.seed}"
          + ("  stratified by condition x model" if args.stratify else "  simple random"))
    print(f"  code/notes/coder/coded_at cleared; {already} of these are coded on the "
          "primary sheet")
    comp: dict[str, int] = {}
    for i in picked:
        key = f"{rows[i].get('condition','?')}/{rows[i].get('model','?')}"
        comp[key] = comp.get(key, 0) + 1
    print("  composition: " + ", ".join(f"{k}={v}" for k, v in sorted(comp.items())))
    print(f"\nnext: python src\\code_items.py --sheet {out} --coder <second coder>")
    return 0


# ------------------------------------------------------------------------- alpha

def cmd_alpha(args: argparse.Namespace) -> int:
    primary, secondary = read_sheet(args.primary), read_sheet(args.secondary)
    p_by_key = {unit_key(r): r for r in primary}

    units: list[list[int]] = []
    disagreements = []
    missing_primary = one_sided = 0

    for row in secondary:
        key = unit_key(row)
        base = p_by_key.get(key)
        if base is None:
            missing_primary += 1
            continue
        a, b = code_of(base), code_of(row)
        if a is None or b is None:
            one_sided += 1          # blank or EXCLUDE on either side: no pair to compare
            continue
        units.append([RANK[a], RANK[b]])
        if a != b:
            disagreements.append((key, a, b, abs(RANK[a] - RANK[b]), base, row))

    n = len(units)
    print(f"# Inter-coder reliability\n")
    print(f"primary:   {args.primary}")
    print(f"secondary: {args.secondary}\n")
    print(f"overlapping units compared: {n}")
    if missing_primary:
        print(f"  {missing_primary} secondary row(s) had no matching primary row")
    if one_sided:
        print(f"  {one_sided} pair(s) skipped: blank or EXCLUDE on one side")
    if n == 0:
        print("\nNothing to compare yet. Both sheets must be coded first.")
        return 1

    agreed = sum(1 for u in units if u[0] == u[1])
    print(f"\nobserved agreement: {agreed}/{n} = {agreed/n:.0%}  "
          f"(chance is not removed here; that is what alpha is for)")

    for metric in ("ordinal", "nominal"):
        a = krippendorff(units, len(CODES), metric)
        if a is None:
            print(f"\nalpha ({metric}): undefined -- every rating fell in one category.")
            continue
        line = f"\nalpha ({metric}): {a:.3f}"
        ci = bootstrap_ci(units, len(CODES), metric, args.seed, args.reps)
        if ci:
            line += f"   95% CI [{ci[0]:.3f}, {ci[1]:.3f}]  (unit bootstrap, {args.reps} reps)"
        print(line)

    ordinal = krippendorff(units, len(CODES), "ordinal")
    print("\nOrdinal is the one to report: the ladder is ordered, and a "
          "faithful/reversal\nsplit is a worse failure than faithful/filler.")

    if disagreements:
        print(f"\n## Disagreements ({len(disagreements)}/{n})\n")
        print("| item | model | primary | secondary | rank gap |")
        print("|---|---|---|---|---|")
        for (item, model, _), a, b, gap, _, _ in sorted(
                disagreements, key=lambda d: -d[3]):
            print(f"| {item} | {model} | {a} | {b} | {gap} |")
        if args.verbose:
            print()
            for (item, _, _), a, b, _, base, row in sorted(
                    disagreements, key=lambda d: -d[3]):
                print(f"--- {item}")
                print(f"    keywords:  {base.get('keywords_keep_please','')}")
                print(f"    expansion: {base.get('expansion','')}")
                print(f"    {a:12s} {base.get('notes','')}")
                print(f"    {b:12s} {row.get('notes','')}")
    else:
        print("\nNo disagreements.")

    if ordinal is None:
        return 1
    print()
    if ordinal < THRESHOLD:
        print(f"BELOW THRESHOLD: {ordinal:.3f} < {THRESHOLD}. The codebook says revise "
              "to v1.1\nand recode the whole sample -- not just the disputed rows.")
        return 1
    print(f"At or above the codebook threshold ({ordinal:.3f} >= {THRESHOLD}). "
          "Report alpha in the paper\nwith n and the metric, not on its own.")
    return 0


# -------------------------------------------------------------------- self-check

def cmd_self_check() -> int:
    """Regression values on a 12-unit, 3-observer matrix with missing data.

    The nominal value is hand-derivable, which is why it is here: the coincidence
    matrix has margins (5, 10, 8, 3, 2) over n = 28 with 7 units of off-diagonal
    mass, so Do = 7/28 = 0.25 and De = (28^2 - 202)/(28*27) = 0.769841, giving
    1 - 0.25/0.769841 = 0.675258. The ordinal value was fixed by cross-checking
    against the `krippendorff` PyPI package, which agrees with this file to 2e-16
    across 600 randomised cases; when that package is installed the comparison is
    re-run here rather than trusted.
    """
    obs = [
        [1, 2, 3, 3, 2, 1, 4, 1, 2, None, None, None],
        [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, None, 3],
        [None, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, None],
    ]
    units = []
    for u in range(12):
        vals = [o[u] - 1 for o in obs if o[u] is not None]
        if len(vals) >= 2:
            units.append(vals)

    ok = True

    def check(label: str, got: float | None, expected: float | None,
              tol: float = 5e-6) -> None:
        nonlocal ok
        if expected is None:
            good = got is None
        else:
            good = got is not None and abs(got - expected) < tol
        ok &= good
        shown = "undefined" if got is None else f"{got:.6f}"
        want = "undefined" if expected is None else f"{expected:.6f}"
        print(f"  {label:10s} expected {want:>9s}  got {shown:>9s}  "
              f"{'OK' if good else 'MISMATCH'}")

    check("nominal", krippendorff(units, 5, "nominal"), 0.675258)
    check("ordinal", krippendorff(units, 5, "ordinal"), 0.804861)
    check("perfect", krippendorff([[0, 0], [1, 1], [4, 4], [2, 2]], 5, "ordinal"), 1.0)
    check("one-cat", krippendorff([[0, 0], [0, 0]], 5, "ordinal"), None)

    try:  # optional: compare against the reference implementation if it is present
        import numpy as np
        import krippendorff as ref
    except ImportError:
        print("\n  (`pip install krippendorff` to also cross-check against the "
              "reference implementation)")
    else:
        arr = np.array([[np.nan if v is None else float(v) for v in row]
                        for row in obs], dtype=float)
        for metric in ("nominal", "ordinal"):
            got = krippendorff(units, 5, metric)
            want = float(ref.alpha(reliability_data=arr, level_of_measurement=metric,
                                   value_domain=[1, 2, 3, 4, 5]))
            check(f"ref/{metric}", got, want, tol=1e-9)

    print("\nself-check:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-check", action="store_true",
                        help="verify alpha against the published worked example")
    sub = parser.add_subparsers(dest="cmd")

    d = sub.add_parser("draw", help="write a blank second-coder subsample")
    d.add_argument("--sheet", required=True, type=Path)
    d.add_argument("--out", type=Path, default=None)
    d.add_argument("--frac", type=float, default=0.2, help="codebook says 20%%")
    d.add_argument("--n", type=int, default=None, help="exact row count, overrides --frac")
    d.add_argument("--seed", type=int, default=config.SEED)
    d.add_argument("--stratify", action="store_true",
                   help="balance across condition x model (codebook says plain random)")
    d.add_argument("--force", action="store_true", help="overwrite an existing out file")
    d.set_defaults(func=cmd_draw)

    a = sub.add_parser("alpha", help="Krippendorff's alpha between two sheets")
    a.add_argument("--primary", required=True, type=Path)
    a.add_argument("--secondary", required=True, type=Path)
    a.add_argument("--seed", type=int, default=config.SEED)
    a.add_argument("--reps", type=int, default=2000, help="bootstrap resamples")
    a.add_argument("--verbose", action="store_true",
                   help="print the text and both coders' notes for each disagreement")
    a.set_defaults(func=cmd_alpha)

    args = parser.parse_args()
    if args.self_check:
        return cmd_self_check()
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
