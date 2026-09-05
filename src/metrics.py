r"""Metrics for RQ1 (fidelity), RQ2 (style drift), RQ3 (unlicensed additions).

Reads an expansions JSONL from generate.py and writes tidy CSVs into results/.
No number reaches the paper unless it came out of one of these files.

RQ1 -- semantic fidelity (D4): cosine(source, expansion) with config.EMBEDDING_MODEL.

RQ2 -- style drift (D5): five features computed on the source and on the expansion,
reported as both raw values and expansion-minus-source deltas:
  length_ratio, lexical_density, hedge_rate, first_person_rate, type_token_ratio
"Content word" is imported from compress.py, so lexical density and the compression
rule cannot drift apart. hedge_rate needs src/hedges.txt (D5: RajC curates it from a
published lexicon and cites it); without that file the column is NaN and everything
else still runs.
Plus the Agarwal-style convergence check: mean pairwise similarity among expansions
within a condition vs. among the sources of that condition. Expansions more alike
than their sources were = homogenization.

RQ3 -- unlicensed additions (D6): each expansion is split into clauses and each clause
is run through config.NLI_MODEL against the source as premise. Clauses whose top label
is not "entailment" are flagged. These flags only prioritize -- RajC's hand-coding is
the ground truth (D7).

Paired analysis (D8): items are matched by the numeric part of the id, so aut-014
pairs with ctl-014. Statistics are Wilcoxon signed-rank on within-pair differences
with matched-pairs rank-biserial effect sizes. The k samples of an item are averaged
before pairing, so one pair contributes one difference.

Outputs (run_id taken from the input filename):
  metrics_<run_id>.csv          one row per generation, every metric
  paired_stats_<run_id>.csv     one row per (metric, model): n, medians, W, p, effect
  convergence_<run_id>.csv      one row per (set, model): source vs expansion spread
  handcode_sample_<run_id>.csv  stratified sample for RajC, empty rubric columns

CLI:
  python src\metrics.py --in results\expansions_<run_id>.jsonl
  python src\metrics.py --in ... --no-nli       # skip RQ3 (slowest stage)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
from compress import _is_content, _nlp  # noqa: E402  (one definition of "content word")

HEDGE_FILE = config.ROOT / "src" / "hedges.txt"
FIRST_PERSON = {"i", "me", "my", "mine", "myself"}

# D7 rubric: an ordered ladder of increasing severity, coded worst-wins (one code per
# item). Frozen 2026-09-05, before any generation run existed. `notes` is mandatory for
# any code above `faithful` -- that is where the multi-label information is recovered
# qualitatively, and where the paper's examples come from.
HANDCODE_CATEGORIES = {
    1: "faithful",
    2: "filler",
    3: "unlicensed",
    4: "tone_shift",
    5: "reversal",
}
HANDCODE_COLUMNS = ["code", "notes"]

# Multiple comparisons (D10): six tests per model. Holm-Bonferroni is reported
# alongside raw p, and the confirmatory headline test is the composite below.
BOOTSTRAP_N = 2000


def holm(pvalues: list[float]) -> list[float]:
    """Holm-Bonferroni step-down adjusted p-values, in the input order."""
    import numpy as np

    p = np.asarray(pvalues, dtype=float)
    order = np.argsort(p)
    m = len(p)
    adjusted = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * p[idx])
        adjusted[idx] = min(running, 1.0)
    return adjusted.tolist()


def bootstrap_rank_biserial(diffs, n_boot: int = BOOTSTRAP_N) -> tuple[float, float]:
    """Percentile CI for the matched-pairs rank-biserial correlation (seeded)."""
    import numpy as np
    from scipy import stats

    d = np.asarray([x for x in diffs if x == x], dtype=float)
    if len(d) < 6:
        return float("nan"), float("nan")
    rng = np.random.default_rng(config.SEED)
    estimates = []
    for _ in range(n_boot):
        sample = rng.choice(d, size=len(d), replace=True)
        nz = sample[sample != 0]
        if len(nz) < 2:
            continue
        ranks = stats.rankdata(np.abs(nz))
        r_pos, r_neg = ranks[nz > 0].sum(), ranks[nz < 0].sum()
        estimates.append((r_pos - r_neg) / (r_pos + r_neg))
    if len(estimates) < 100:
        return float("nan"), float("nan")
    return (float(np.percentile(estimates, 2.5)),
            float(np.percentile(estimates, 97.5)))


def stats_spearman(x, y) -> float:
    from scipy import stats

    return float(stats.spearmanr(x, y).statistic)


def drift_composite(df):
    """D5 composite: mean z-scored magnitude of change across the five features.

    Drift is defined direction-agnostically as distance from "no change" -- |ratio - 1|
    for length_ratio and |delta| for the four delta features -- so the composite needs
    no sign-alignment judgement. Each component is z-scored across the whole run before
    averaging, so features on different scales contribute equally. Components that are
    entirely NaN (e.g. hedge_rate with no lexicon) drop out.
    """
    import numpy as np

    parts = []
    for col, ref in [("length_ratio", 1.0), ("d_lexical_density", 0.0),
                     ("d_hedge_rate", 0.0), ("d_first_person_rate", 0.0),
                     ("d_type_token_ratio", 0.0)]:
        if col not in df.columns or not df[col].notna().any():
            continue
        magnitude = (df[col] - ref).abs()
        sd = magnitude.std()
        if sd and sd == sd:
            parts.append((magnitude - magnitude.mean()) / sd)
    if not parts:
        return None
    return sum(parts) / len(parts)

PAIR_ID_RE = re.compile(r"(\d+)")

# Polarity. Negation is carried almost entirely by function words (no, not, n't,
# never), which the D1 content-word rule removes, so a refusal can reach the model as
# an affirmative keyword set. Tracked per row because an AAC system that turns "no"
# into "yes" is a different and more serious failure than a register shift.
NEGATION_RE = re.compile(
    r"\b(?:no|not|never|none|nothing|nobody|cannot|dont|doesnt|isnt|wasnt|wont|cant)\b"
    r"|n't", re.IGNORECASE)


def has_negation(text: str) -> bool:
    return bool(NEGATION_RE.search(text or ""))


# --- helpers -----------------------------------------------------------------

def pair_id(item_id: str) -> str | None:
    """aut-014 / ctl-014 -> "014". None if the id carries no number."""
    m = PAIR_ID_RE.search(item_id or "")
    return m.group(1) if m else None


def load_hedges() -> list[str] | None:
    """Hedge terms, one per line, # comments allowed. None if RajC has not written it."""
    if not HEDGE_FILE.exists():
        return None
    terms = []
    for line in HEDGE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip().lower()
        if line:
            terms.append(line)
    return terms


def read_jsonl(path: Path) -> list[dict]:
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


# --- RQ2: style features -----------------------------------------------------

def style_features(text: str, hedges: list[str] | None) -> dict:
    """The five D5 features for one string. length is reported as a raw count;
    the ratio is formed later against the matching source."""
    doc = _nlp()(text)
    words = [t for t in doc if not t.is_punct and not t.is_space]
    n = len(words)
    if n == 0:
        return {"n_tokens": 0, "lexical_density": float("nan"),
                "hedge_rate": float("nan"), "first_person_rate": float("nan"),
                "type_token_ratio": float("nan")}

    lowered = [t.text.lower() for t in words]
    content = sum(1 for t in words if _is_content(t))
    first_person = sum(1 for w in lowered if w in FIRST_PERSON)
    types = len(set(lowered))

    if hedges is None:
        hedge_rate = float("nan")
    else:
        # Count hedge terms as phrases against the normalised text, so multi-word
        # hedges ("sort of", "a bit") are matched, then express per token.
        norm = " " + " ".join(lowered) + " "
        hits = sum(norm.count(" " + h + " ") for h in hedges)
        hedge_rate = hits / n

    return {
        "n_tokens": n,
        "lexical_density": content / n,
        "hedge_rate": hedge_rate,
        "first_person_rate": first_person / n,
        "type_token_ratio": types / n,
    }


# --- RQ3: clause splitting ---------------------------------------------------

def split_clauses(text: str) -> list[str]:
    """Split an expansion into clauses for clause-level entailment.

    Sentences first, then top-level coordinated verb phrases (dep_ == "conj" on a
    verbal head), which is where "and I would love to join you" style additions show
    up. Granularity affects the RQ3 rate, so it is one function on purpose and the
    per-clause text is written to the CSV for RajC to check against.
    """
    doc = _nlp()(text)
    clauses: list[str] = []
    for sent in doc.sents:
        cut_points = sorted(
            tok.left_edge.i
            for tok in sent
            if tok.dep_ == "conj" and tok.head.pos_ in ("VERB", "AUX")
            and tok.pos_ in ("VERB", "AUX") and tok.left_edge.i > sent.start
        )
        starts = [sent.start] + cut_points
        ends = cut_points + [sent.end]
        for s, e in zip(starts, ends):
            chunk = doc[s:e].text.strip(" ,;")
            if chunk:
                clauses.append(chunk)
    return clauses or [text.strip()]


# --- stats -------------------------------------------------------------------

def wilcoxon_paired(diffs) -> dict:
    """Wilcoxon signed-rank + matched-pairs rank-biserial correlation."""
    import numpy as np
    from scipy import stats

    d = np.asarray([x for x in diffs if x == x], dtype=float)  # drop NaN
    nonzero = d[d != 0]
    out = {"n_pairs": int(len(d)), "n_nonzero": int(len(nonzero)),
           "median_diff": float(np.median(d)) if len(d) else float("nan"),
           "W": float("nan"), "p": float("nan"), "rank_biserial": float("nan")}
    if len(nonzero) < 6:  # too few to say anything; report and move on
        return out

    res = stats.wilcoxon(nonzero, alternative="two-sided")
    ranks = stats.rankdata(np.abs(nonzero))
    r_pos = ranks[nonzero > 0].sum()
    r_neg = ranks[nonzero < 0].sum()
    out["W"] = float(res.statistic)
    out["p"] = float(res.pvalue)
    out["rank_biserial"] = float((r_pos - r_neg) / (r_pos + r_neg))
    return out


def mean_pairwise_cosine(vectors) -> float:
    """Mean off-diagonal cosine of a set of unit-normalised vectors."""
    import numpy as np

    if len(vectors) < 2:
        return float("nan")
    m = np.asarray(vectors, dtype=float)
    sims = m @ m.T
    n = len(m)
    return float((sims.sum() - np.trace(sims)) / (n * (n - 1)))


# --- main --------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="in_path", required=True, type=Path)
    parser.add_argument("--out-dir", type=Path, default=config.RESULTS)
    parser.add_argument("--no-nli", action="store_true", help="skip RQ3")
    parser.add_argument("--include-refusals", action="store_true",
                        help="keep refusal_like rows in the paired statistics")
    args = parser.parse_args()

    import numpy as np
    import pandas as pd
    import torch
    from sentence_transformers import CrossEncoder, SentenceTransformer

    run_id = args.in_path.stem.replace("expansions_", "")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    records = read_jsonl(args.in_path)
    if not records:
        raise SystemExit(f"{args.in_path}: no records")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    hedges = load_hedges()
    if hedges is None:
        print(f"WARN {HEDGE_FILE.name} not found: hedge_rate will be NaN "
              "(D5 -- RajC curates it from a published lexicon)")

    print(f"run_id {run_id}: {len(records)} generations, device {device}")

    # --- RQ1: fidelity ---
    embedder = SentenceTransformer(config.EMBEDDING_MODEL, device=device)
    sources = [r.get("source_text") or "" for r in records]
    expansions = [r.get("expansion") or "" for r in records]
    uniq_src = sorted(set(sources))
    src_vecs = embedder.encode(uniq_src, normalize_embeddings=True,
                               batch_size=64, show_progress_bar=False)
    src_index = {t: v for t, v in zip(uniq_src, src_vecs)}
    exp_vecs = embedder.encode(expansions, normalize_embeddings=True,
                               batch_size=64, show_progress_bar=True)

    # --- RQ2 + RQ3 per row ---
    nli = None
    if not args.no_nli:
        nli = CrossEncoder(config.NLI_MODEL, device=device)
        id2label = {int(k): v.lower() for k, v in nli.model.config.id2label.items()}
        print(f"NLI labels: {id2label}")

    rows = []
    for rec, exp_vec in zip(records, exp_vecs):
        src, exp = rec.get("source_text") or "", rec.get("expansion") or ""
        sf_src = style_features(src, hedges)
        sf_exp = style_features(exp, hedges)

        row = {
            "run_id": rec.get("run_id"), "id": rec.get("id"),
            "pair_id": pair_id(rec.get("id") or ""), "set": rec.get("set"),
            "topic": rec.get("topic"),
            "style_tags": "|".join(rec.get("style_tags") or []),
            "model": rec.get("model"), "sample_idx": rec.get("sample_idx"),
            "seed": rec.get("seed"), "refusal_like": bool(rec.get("refusal_like")),
            "source_text": src, "keywords": " ".join(rec.get("keywords") or []),
            "expansion": exp,
            "fidelity_cosine": float(np.dot(src_index[src], exp_vec)),
            "length_ratio": (sf_exp["n_tokens"] / sf_src["n_tokens"]
                             if sf_src["n_tokens"] else float("nan")),
        }
        for feat in ("lexical_density", "hedge_rate", "first_person_rate",
                     "type_token_ratio"):
            row[f"src_{feat}"] = sf_src[feat]
            row[f"exp_{feat}"] = sf_exp[feat]
            row[f"d_{feat}"] = sf_exp[feat] - sf_src[feat]
        row["src_n_tokens"] = sf_src["n_tokens"]
        row["exp_n_tokens"] = sf_exp["n_tokens"]
        src_neg = has_negation(src)
        exp_neg = has_negation(exp)
        row["src_has_negation"] = src_neg
        row["keywords_has_negation"] = has_negation(" ".join(rec.get("keywords") or []))
        row["exp_has_negation"] = exp_neg
        # True only where the source was negated and the expansion is not: the
        # polarity of the utterance was inverted somewhere in the pipeline.
        row["polarity_lost"] = bool(src_neg and not exp_neg)

        if nli is not None:
            clauses = split_clauses(exp)
            scores = nli.predict([(src, c) for c in clauses], show_progress_bar=False)
            labels = [id2label[int(np.argmax(s))] for s in np.atleast_2d(scores)]
            unentailed = [c for c, lab in zip(clauses, labels) if lab != "entailment"]
            row["n_clauses"] = len(clauses)
            row["n_unentailed"] = len(unentailed)
            row["unentailed_rate"] = len(unentailed) / len(clauses)
            row["n_contradiction"] = sum(1 for lab in labels if lab == "contradiction")
            row["clauses"] = " || ".join(clauses)
            row["unentailed_clauses"] = " || ".join(unentailed)
        rows.append(row)

    df = pd.DataFrame(rows)
    # computed before the CSV is written, so the confirmatory measure is traceable
    composite_all = drift_composite(df)
    if composite_all is not None:
        df["drift_composite"] = composite_all
    metrics_path = args.out_dir / f"metrics_{run_id}.csv"
    df.to_csv(metrics_path, index=False, encoding="utf-8")
    print(f"\nwrote {metrics_path}  ({len(df)} rows)")

    # --- paired statistics (D8) ---
    analysed = df if args.include_refusals else df[~df["refusal_like"]]
    n_dropped = len(df) - len(analysed)
    if n_dropped:
        print(f"paired stats exclude {n_dropped} refusal_like row(s) "
              "(--include-refusals to keep them)")

    metric_cols = ["fidelity_cosine", "length_ratio"] + [
        f"d_{f}" for f in ("lexical_density", "hedge_rate", "first_person_rate",
                           "type_token_ratio")
    ]
    if "unentailed_rate" in analysed.columns:
        metric_cols.append("unentailed_rate")
    if "drift_composite" in analysed.columns:
        metric_cols.append("drift_composite")

    # average the k samples first, so one item contributes one value
    per_item = (analysed.groupby(["model", "set", "pair_id"], dropna=True)[metric_cols]
                .mean().reset_index())

    stat_rows = []
    skipped: set[str] = set()
    for model in sorted(per_item["model"].dropna().unique()):
        sub = per_item[per_item["model"] == model]
        aut = sub[sub["set"] == "autistic_style"].set_index("pair_id")
        ctl = sub[sub["set"] == "control_style"].set_index("pair_id")
        shared = sorted(set(aut.index) & set(ctl.index))
        if not shared:
            print(f"WARN {model}: no matched aut/ctl pairs found "
                  "(need both sets in one run, ids sharing a number)")
            continue
        for metric in metric_cols:
            a, c = aut.loc[shared, metric], ctl.loc[shared, metric]
            if not (a.notna().any() and c.notna().any()):
                skipped.add(metric)  # e.g. hedge_rate with no hedges.txt
                continue
            diffs = (a - c).to_numpy()
            res = wilcoxon_paired(diffs)
            lo, hi = bootstrap_rank_biserial(diffs)
            stat_rows.append({
                "model": model, "metric": metric,
                # the composite is the one confirmatory test (D10); the rest are
                # exploratory and carry the Holm-adjusted column
                "role": "confirmatory" if metric == "drift_composite" else "exploratory",
                "median_autistic": float(np.nanmedian(a)),
                "median_control": float(np.nanmedian(c)),
                **res,
                "rank_biserial_ci_low": lo, "rank_biserial_ci_high": hi,
            })
    # Length-adjusted confirmatory test. Hedged control sources are longer than direct
    # autistic ones by construction -- hedging IS extra words -- and under a fixed
    # keyword cap a longer source has further to fall. The composite therefore
    # correlates with source length, so the same test is repeated on the composite
    # residualised on source token count, and both rows are reported.
    if "drift_composite" in analysed.columns and "src_n_tokens" in analysed.columns:
        for model in sorted(analysed["model"].dropna().unique()):
            s = analysed[(analysed["model"] == model)].dropna(
                subset=["drift_composite", "src_n_tokens"])
            if len(s) < 12:
                continue
            slope, intercept = np.polyfit(s["src_n_tokens"], s["drift_composite"], 1)
            resid = s["drift_composite"] - (intercept + slope * s["src_n_tokens"])
            per = (s.assign(_r=resid).groupby(["set", "pair_id"])["_r"]
                   .mean().reset_index())
            a = per[per["set"] == "autistic_style"].set_index("pair_id")["_r"]
            c = per[per["set"] == "control_style"].set_index("pair_id")["_r"]
            shared = sorted(set(a.index) & set(c.index))
            if not shared:
                continue
            diffs = (a.loc[shared] - c.loc[shared]).to_numpy()
            res = wilcoxon_paired(diffs)
            lo, hi = bootstrap_rank_biserial(diffs)
            rho = stats_spearman(s["src_n_tokens"], s["drift_composite"])
            stat_rows.append({
                "model": model, "metric": "drift_composite_length_adjusted",
                "role": "confirmatory",
                "median_autistic": float(np.nanmedian(a.loc[shared])),
                "median_control": float(np.nanmedian(c.loc[shared])),
                **res,
                "rank_biserial_ci_low": lo, "rank_biserial_ci_high": hi,
                "spearman_composite_vs_source_length": rho,
            })

    if skipped:
        print(f"paired stats skipped (no data): {', '.join(sorted(skipped))}")
    if stat_rows:
        stats_df = pd.DataFrame(stat_rows)
        # Holm family = the exploratory tests within one model (D10). The confirmatory
        # composite is one pre-specified test and is not corrected.
        stats_df["p_holm"] = float("nan")
        for model, sub in stats_df.groupby("model"):
            expl = sub[(sub["role"] == "exploratory") & sub["p"].notna()]
            if len(expl):
                stats_df.loc[expl.index, "p_holm"] = holm(expl["p"].tolist())
        stats_path = args.out_dir / f"paired_stats_{run_id}.csv"
        stats_df.to_csv(stats_path, index=False, encoding="utf-8")
        n_conf = int((stats_df["role"] == "confirmatory").sum())
        print(f"wrote {stats_path}  ({len(stats_df)} tests: {n_conf} confirmatory "
              f"(composite, uncorrected), {len(stats_df) - n_conf} exploratory "
              "with raw and Holm-adjusted p)")

    # --- convergence (Agarwal-style) ---
    conv_rows = []
    for (rset, model), sub in analysed.groupby(["set", "model"], dropna=True):
        uniq = sub.drop_duplicates("id")
        s_vecs = [src_index[t] for t in uniq["source_text"]]
        e_vecs = embedder.encode(sub["expansion"].tolist(), normalize_embeddings=True,
                                 batch_size=64, show_progress_bar=False)
        src_sim = mean_pairwise_cosine(s_vecs)
        exp_sim = mean_pairwise_cosine(e_vecs)
        conv_rows.append({
            "set": rset, "model": model, "n_items": len(uniq),
            "n_expansions": len(sub),
            "mean_pairwise_cosine_sources": src_sim,
            "mean_pairwise_cosine_expansions": exp_sim,
            "convergence_delta": exp_sim - src_sim,
        })
    if conv_rows:
        conv_path = args.out_dir / f"convergence_{run_id}.csv"
        pd.DataFrame(conv_rows).to_csv(conv_path, index=False, encoding="utf-8")
        print(f"wrote {conv_path}  (positive convergence_delta = homogenization)")

    # --- hand-coding export (D7) ---
    rng = np.random.default_rng(config.SEED)
    # At most one generation per (item, model): the k samples of an item are often
    # byte-identical, so drawing several wastes coding effort on the same string and
    # double-weights that item in the code distribution. One draw per cell, seeded,
    # maximises item coverage instead.
    pool = (df.groupby(["id", "model"], dropna=False, group_keys=False)
            .sample(n=1, random_state=config.SEED)
            .reset_index(drop=True))
    strata = ["set", "model"]
    if "n_unentailed" in pool.columns:
        pool["_flagged"] = pool["n_unentailed"] > 0
        strata.append("_flagged")
    groups = [g for _, g in pool.groupby(strata, dropna=False)]
    per_group = max(1, config.HANDCODE_SAMPLE_SIZE // max(len(groups), 1))
    picks = []
    for g in groups:
        take = min(per_group, len(g))
        picks.append(g.iloc[rng.choice(len(g), size=take, replace=False)])
    sample = pd.concat(picks).sort_values(["set", "model", "id", "sample_idx"])
    keep = ["id", "set", "model", "sample_idx", "source_text", "keywords", "expansion"]
    if "unentailed_clauses" in sample.columns:
        keep += ["n_clauses", "n_unentailed", "unentailed_clauses"]
    sample = sample[keep].copy()
    # D7 export shape: item_id / condition / model / code / notes, worst-wins.
    sample = sample.rename(columns={"id": "item_id", "set": "condition"})
    for col in HANDCODE_COLUMNS:
        sample[col] = ""
    hc_path = args.out_dir / f"handcode_sample_{run_id}.csv"
    sample.to_csv(hc_path, index=False, encoding="utf-8")
    print(f"wrote {hc_path}  ({len(sample)} items, stratified by "
          f"{', '.join(s.lstrip('_') for s in strata)}, seed {config.SEED})")
    print("  D7 codes (worst-wins): "
          + ", ".join(f"{k}={v}" for k, v in HANDCODE_CATEGORIES.items()))
    print("  notes is mandatory for any code above faithful")


if __name__ == "__main__":
    main()
