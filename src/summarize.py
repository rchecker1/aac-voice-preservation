r"""Emit every headline number for one run as a single markdown file.

The point is that Results can be written from one page, and that each number in the
paper has exactly one place it came from. Nothing here computes anything new -- it
reads the CSVs metrics.py wrote and formats them. No interpretation, no captions.

Flags two classes of number that must not be reported as findings:
- effects with a zero-width bootstrap CI at |1.000|, which are produced by the rule
  rather than found in the data (e.g. hedge rate under --strip-register);
- the raw composite when it is strongly correlated with source length.

CLI: python src\summarize.py --run results\keep_please
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def fmt(x, nd=3) -> str:
    try:
        if x != x:
            return "—"
        return f"{x:.{nd}f}"
    except (TypeError, ValueError):
        return str(x)


def agreement_block(run_dir: Path, hc_path: Path) -> list[str]:
    """NLI flags vs RajC's hand codes (D6: flags only prioritise, codes are truth).

    The question is whether the automatic flag is a usable triage signal, so this
    reports the 2x2 against "code above faithful", with precision, recall and Cohen's
    kappa. Low precision is not a failure of the study -- it is the reason D6 says
    hand-coding is the ground truth -- but it needs stating either way.
    """
    import pandas as pd

    hc = pd.read_csv(hc_path)
    hc = hc[hc["code"].astype(str).str.strip() != ""]
    if not len(hc):
        return ["## NLI vs hand codes", "", "No filled-in codes yet.", ""]

    if "n_unentailed" not in hc.columns:
        return ["## NLI vs hand codes", "",
                "Export has no NLI columns; re-run metrics without --no-nli.", ""]

    hc["nli_flag"] = hc["n_unentailed"] > 0
    hc["hand_flag"] = hc["code"].astype(str).str.strip().str.lower() != "faithful"

    tp = int((hc.nli_flag & hc.hand_flag).sum())
    fp = int((hc.nli_flag & ~hc.hand_flag).sum())
    fn = int((~hc.nli_flag & hc.hand_flag).sum())
    tn = int((~hc.nli_flag & ~hc.hand_flag).sum())
    n = tp + fp + fn + tn
    precision = tp / (tp + fp) if tp + fp else float("nan")
    recall = tp / (tp + fn) if tp + fn else float("nan")
    po = (tp + tn) / n if n else float("nan")
    pe = (((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / (n * n)) if n else float("nan")
    kappa = (po - pe) / (1 - pe) if pe not in (1.0,) and pe == pe else float("nan")

    out = ["## NLI flags vs hand codes", "",
           "Hand codes are the ground truth (D6); the flag only prioritises.", "",
           "| | hand: not faithful | hand: faithful |", "|---|---|---|",
           f"| NLI flagged | {tp} | {fp} |",
           f"| NLI clear | {fn} | {tn} |", "",
           f"- coded items: {n}",
           f"- precision {fmt(precision, 2)}, recall {fmt(recall, 2)}, "
           f"Cohen's kappa {fmt(kappa, 2)}", ""]

    counts = hc["code"].astype(str).str.strip().value_counts()
    out += ["### Code distribution (worst-wins)", "",
            "| code | n | share |", "|---|---|---|"]
    for code, k in counts.items():
        out.append(f"| {code} | {k} | {fmt(k / len(hc), 2)} |")
    out.append("")

    if "condition" in hc.columns:
        out += ["### By condition", "", "| condition | n | share not faithful |",
                "|---|---|---|"]
        for cond, sub in hc.groupby("condition"):
            out.append(f"| {cond} | {len(sub)} | {fmt(sub['hand_flag'].mean(), 2)} |")
        out.append("")

    missing = hc[hc["hand_flag"] & (hc.get("notes", "").astype(str).str.strip() == "")]
    if len(missing):
        out.append(f"**{len(missing)} item(s) coded above `faithful` with no notes** — "
                   "D7 makes notes mandatory there. Ids: "
                   + ", ".join(missing["item_id"].astype(str).head(15)) + "")
        out.append("")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", required=True, type=Path, help="results/<run_id>/")
    parser.add_argument("--handcodes", type=Path,
                        help="filled-in hand-coding CSV; adds the agreement section")
    args = parser.parse_args()

    import pandas as pd

    run_dir = args.run
    run_id = run_dir.name
    stats = pd.read_csv(run_dir / f"paired_stats_{run_id}.csv")
    metrics = pd.read_csv(run_dir / f"metrics_{run_id}.csv")
    conv = pd.read_csv(run_dir / f"convergence_{run_id}.csv")
    manifest_path = run_dir / f"manifest_{run_id}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if \
        manifest_path.exists() else {}

    out = [f"# Run summary — `{run_id}`", ""]
    out.append(f"- compression: "
               f"{'strip-register' if manifest.get('strip_register') else 'keep-please'}")
    out.append(f"- generations: {len(metrics)}   items: {metrics['id'].nunique()}   "
               f"models: {metrics['model'].nunique()}")
    out.append(f"- refusal-flagged: {int(metrics['refusal_like'].sum())}")
    out.append("")

    # --- confirmatory ---
    conf = stats[stats["role"] == "confirmatory"]
    out += ["## Confirmatory test (D5 composite)", "",
            "Negative effect = control items drift more than autistic-style items.", "",
            "| model | test | n | rank-biserial | 95% CI | p |", "|---|---|---|---|---|---|"]
    for _, r in conf.iterrows():
        primary = "**" if r["metric"].endswith("length_adjusted") else ""
        ci = f"[{fmt(r['rank_biserial_ci_low'], 2)}, {fmt(r['rank_biserial_ci_high'], 2)}]"
        out.append(f"| {r['model']} | {primary}{r['metric']}{primary} | {int(r['n_pairs'])} "
                   f"| {fmt(r['rank_biserial'])} | {ci} | {fmt(r['p'], 4)} |")
    rho = conf["spearman_composite_vs_source_length"].dropna()
    if len(rho):
        out += ["", f"Composite vs source length (Spearman): "
                    f"{', '.join(fmt(v, 2) for v in rho)}. The length-adjusted row is "
                    "the primary result (D10)."]
    out.append("")

    # --- exploratory ---
    expl = stats[stats["role"] == "exploratory"]
    out += ["## Exploratory tests (Holm-adjusted within model)", "",
            "| model | metric | median aut | median ctl | rank-biserial | 95% CI | p | p (Holm) |",
            "|---|---|---|---|---|---|---|---|"]
    for _, r in expl.iterrows():
        ci = f"[{fmt(r['rank_biserial_ci_low'], 2)}, {fmt(r['rank_biserial_ci_high'], 2)}]"
        out.append(f"| {r['model']} | {r['metric']} | {fmt(r['median_autistic'])} "
                   f"| {fmt(r['median_control'])} | {fmt(r['rank_biserial'])} | {ci} "
                   f"| {fmt(r['p'], 4)} | {fmt(r['p_holm'], 4)} |")
    out.append("")

    # --- convergence ---
    out += ["## Convergence (positive delta = homogenisation)", "",
            "| set | model | sources | expansions | delta |", "|---|---|---|---|---|"]
    for _, r in conv.iterrows():
        out.append(f"| {r['set']} | {r['model']} "
                   f"| {fmt(r['mean_pairwise_cosine_sources'], 4)} "
                   f"| {fmt(r['mean_pairwise_cosine_expansions'], 4)} "
                   f"| {fmt(r['convergence_delta'], 4)} |")
    out.append("")

    # --- polarity ---
    if "src_has_negation" in metrics.columns:
        neg = metrics[metrics["src_has_negation"]]
        if len(neg):
            out += ["## Polarity survival", "",
                    "Negation is carried by function words, which the D1 content-word "
                    "rule removes.", "",
                    f"- items whose source is negated: {neg['id'].nunique()} "
                    f"({len(neg)} generations)",
                    f"- keyword sets that still carry negation: "
                    f"{int(neg['keywords_has_negation'].sum())} / {len(neg)}",
                    f"- expansions that restore negation: "
                    f"{int(neg['exp_has_negation'].sum())} / {len(neg)} "
                    f"({fmt(neg['exp_has_negation'].mean() * 100, 0)}%)",
                    f"- **polarity lost: {fmt(neg['polarity_lost'].mean() * 100, 0)}% "
                    "of negated utterances come back affirmative**", ""]
            out += ["| condition | negated generations | polarity lost | "
                    "mean fidelity (negated) | mean fidelity (rest) |",
                    "|---|---|---|---|---|"]
            for cond, sub in metrics.groupby("set"):
                sn = sub[sub["src_has_negation"]]
                if not len(sn):
                    continue
                out.append(f"| {cond} | {len(sn)} | {fmt(sn['polarity_lost'].mean(), 2)} "
                           f"| {fmt(sn['fidelity_cosine'].mean())} "
                           f"| {fmt(sub[~sub['src_has_negation']]['fidelity_cosine'].mean())} |")
            out.append("")

    # --- do-not-report flags ---
    flags = []
    for _, r in stats.iterrows():
        lo, hi = r["rank_biserial_ci_low"], r["rank_biserial_ci_high"]
        if lo == lo and abs(lo) == 1.0 and lo == hi:
            flags.append(f"`{r['metric']}` ({r['model']}): effect 1.000 with a "
                         "zero-width CI — produced by the compression rule, not "
                         "measured. Do not report as a finding.")
    if len(rho) and (rho.abs() > 0.3).any():
        flags.append("Raw `drift_composite` correlates with source length; report the "
                     "length-adjusted row as primary and both in the table.")
    if flags:
        out += ["## Do not report as findings", ""] + [f"- {f}" for f in flags] + [""]

    if args.handcodes and args.handcodes.exists():
        out += agreement_block(run_dir, args.handcodes)

    out += ["---", "",
            f"Generated by `src/summarize.py` from the CSVs in `{run_dir.as_posix()}`. "
            "Every number above is in one of those files."]

    path = run_dir / f"summary_{run_id}.md"
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {path}")
    if flags:
        print(f"  {len(flags)} do-not-report flag(s)")


if __name__ == "__main__":
    main()
