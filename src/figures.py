r"""Figures for the paper, built only from the CSVs metrics.py wrote.

Nothing here interprets anything: titles name the quantity, axes are labelled, and
the captions are RajC's to write. If a number appears in a figure it came out of
results/, never out of this file.

Four figures, one per research question plus convergence:
  fidelity_by_condition.png  RQ1  cosine(source, expansion), per model and condition
  drift_by_condition.png     RQ2  the five D5 feature deltas, small multiples
  additions_rates.png        RQ3  un-entailed clause rate; D7 category rates if coded
  convergence.png            RQ2  source vs expansion spread, per set and model

Colour means condition everywhere (blue = autistic_style, orange = control_style),
with marker shape as a second channel so the figures survive greyscale printing.
Jitter is seeded from config.SEED, so re-running reproduces the same picture.

CLI:
  python src\figures.py --in results\metrics_<run_id>.csv
  python src\figures.py --in ... --handcodes results\handcode_sample_<run_id>.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
from metrics import HANDCODE_CATEGORIES  # noqa: E402

# Reference palette, light surface. Slots 1-2 of the documented categorical order.
BLUE, ORANGE = "#2a78d6", "#eb6834"
SURFACE = "#fcfcfb"
INK, INK_2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"

CONDITIONS = ["autistic_style", "control_style"]
COND_COLOR = {"autistic_style": BLUE, "control_style": ORANGE}
COND_MARKER = {"autistic_style": "o", "control_style": "s"}
COND_LABEL = {"autistic_style": "autistic-style", "control_style": "control"}

FEATURES = [
    ("length_ratio", "length ratio\n(expansion / source)", 1.0),
    ("d_lexical_density", "Δ lexical density", 0.0),
    ("d_hedge_rate", "Δ hedge rate", 0.0),
    ("d_first_person_rate", "Δ first-person rate", 0.0),
    ("d_type_token_ratio", "Δ type-token ratio", 0.0),
]


def _style():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans"],
        "font.size": 9,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": BASELINE,
        "axes.labelcolor": INK_2,
        "axes.titlecolor": INK,
        "axes.titlesize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "legend.frameon": False,
        "savefig.facecolor": SURFACE,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
    })
    return plt


def _box_strip(ax, plt, groups, positions, width=0.5):
    """Box + seeded jittered points for one condition at given x positions."""
    import numpy as np

    rng = np.random.default_rng(config.SEED)
    for (cond, values), pos in zip(groups, positions):
        vals = np.asarray([v for v in values if v == v], dtype=float)
        if len(vals) == 0:
            continue
        color = COND_COLOR[cond]
        bp = ax.boxplot([vals], positions=[pos], widths=width, patch_artist=True,
                        showfliers=False, medianprops={"color": INK, "linewidth": 1.4},
                        whiskerprops={"color": BASELINE, "linewidth": 1.0},
                        capprops={"color": BASELINE, "linewidth": 1.0},
                        boxprops={"linewidth": 0})
        for patch in bp["boxes"]:
            patch.set_facecolor(color)
            patch.set_alpha(0.22)
        jitter = rng.uniform(-width * 0.28, width * 0.28, size=len(vals))
        ax.scatter(pos + jitter, vals, s=11, color=color,
                   marker=COND_MARKER[cond], linewidths=0.5,
                   edgecolors=SURFACE, alpha=0.85, zorder=3)


def _legend(fig, plt, ncol=2):
    from matplotlib.lines import Line2D

    handles = [Line2D([], [], color=COND_COLOR[c], marker=COND_MARKER[c],
                      linestyle="none", markersize=6, label=COND_LABEL[c])
               for c in CONDITIONS]
    fig.legend(handles=handles, loc="lower center", ncol=ncol,
               bbox_to_anchor=(0.5, -0.02), labelcolor=INK_2)


def fig_fidelity(df, out_dir, plt):
    models = sorted(df["model"].dropna().unique())
    fig, ax = plt.subplots(figsize=(1.9 + 1.9 * len(models), 3.4))
    ticks, labels = [], []
    for i, model in enumerate(models):
        base = i * 1.6
        groups, positions = [], []
        for j, cond in enumerate(CONDITIONS):
            sub = df[(df["model"] == model) & (df["set"] == cond)]
            groups.append((cond, sub["fidelity_cosine"].tolist()))
            positions.append(base + (j - 0.5) * 0.62)
        _box_strip(ax, plt, groups, positions)
        ticks.append(base)
        labels.append(model)
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels)
    ax.set_ylabel("cosine(source, expansion)")
    ax.set_title("Semantic fidelity by condition", loc="left", pad=10)
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    _legend(fig, plt)
    path = out_dir / "fidelity_by_condition.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_drift(df, out_dir, plt):
    models = sorted(df["model"].dropna().unique())
    present = [f for f in FEATURES if f[0] in df.columns and df[f[0]].notna().any()]
    if not present:
        return None
    fig, axes = plt.subplots(len(models), len(present),
                             figsize=(2.05 * len(present), 2.5 * len(models)),
                             squeeze=False)
    for r, model in enumerate(models):
        for c, (col, label, ref) in enumerate(present):
            ax = axes[r][c]
            groups, positions = [], []
            for j, cond in enumerate(CONDITIONS):
                sub = df[(df["model"] == model) & (df["set"] == cond)]
                groups.append((cond, sub[col].tolist()))
                positions.append((j - 0.5) * 0.7)
            _box_strip(ax, plt, groups, positions, width=0.52)
            ax.axhline(ref, color=BASELINE, linewidth=1.0, linestyle=(0, (4, 3)),
                       zorder=1)
            ax.set_xticks([])
            ax.yaxis.grid(True)
            ax.set_axisbelow(True)
            if r == 0:
                ax.set_title(label, loc="left", fontsize=9, pad=8)
            if c == 0:
                ax.set_ylabel(model, color=INK, fontsize=9)
    fig.suptitle("Style-feature drift by condition "
                 "(dashed line = no change from source)",
                 x=0.02, ha="left", fontsize=10, color=INK)
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    _legend(fig, plt)
    path = out_dir / "drift_by_condition.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_additions(df, out_dir, plt, handcodes=None):
    import numpy as np

    if "unentailed_rate" not in df.columns:
        return None
    models = sorted(df["model"].dropna().unique())
    n_panels = 1 + (handcodes is not None)
    fig, axes = plt.subplots(1, n_panels, figsize=(4.2 * n_panels, 3.4), squeeze=False)

    ax = axes[0][0]
    ticks, labels = [], []
    for i, model in enumerate(models):
        base = i * 1.6
        groups, positions = [], []
        for j, cond in enumerate(CONDITIONS):
            sub = df[(df["model"] == model) & (df["set"] == cond)]
            groups.append((cond, sub["unentailed_rate"].tolist()))
            positions.append(base + (j - 0.5) * 0.62)
        _box_strip(ax, plt, groups, positions)
        ticks.append(base)
        labels.append(model)
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels)
    ax.set_ylabel("un-entailed clauses / clauses")
    ax.set_title("NLI-flagged additions (automatic)", loc="left", pad=10)
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)

    if handcodes is not None:
        ax = axes[0][1]
        codes = sorted(HANDCODE_CATEGORIES)  # 1..5, ordinal ladder
        width = 0.36
        for j, cond in enumerate(CONDITIONS):
            sub = handcodes[handcodes["condition"] == cond]
            if not len(sub):
                continue
            rates = [(sub["code"] == HANDCODE_CATEGORIES[code]).mean()
                     if sub["code"].dtype == object else
                     (sub["code"] == code).mean() for code in codes]
            xs = np.arange(len(codes)) + (j - 0.5) * width
            ax.bar(xs, rates, width=width * 0.92, color=COND_COLOR[cond],
                   alpha=0.85, linewidth=0)
        ax.set_xticks(np.arange(len(codes)))
        ax.set_xticklabels([f"{c}\n{HANDCODE_CATEGORIES[c].split()[0]}" for c in codes],
                           fontsize=8)
        ax.set_ylabel("share of coded items")
        ax.set_title("Hand-coded categories (D7 ladder)", loc="left", pad=10)
        ax.yaxis.grid(True)
        ax.set_axisbelow(True)

    _legend(fig, plt)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    path = out_dir / "additions_rates.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_convergence(conv, out_dir, plt):
    import numpy as np

    fig, ax = plt.subplots(figsize=(5.6, 0.75 * len(conv) + 1.9))
    rows = conv.sort_values(["model", "set"]).reset_index(drop=True)
    for i, row in rows.iterrows():
        color = COND_COLOR.get(row["set"], MUTED)
        s, e = row["mean_pairwise_cosine_sources"], row["mean_pairwise_cosine_expansions"]
        ax.plot([s, e], [i, i], color=color, linewidth=2.0, alpha=0.55, zorder=1,
                solid_capstyle="round")
        ax.scatter([s], [i], s=48, facecolor=SURFACE, edgecolor=color, linewidths=1.6,
                   marker=COND_MARKER.get(row["set"], "o"), zorder=3)
        ax.scatter([e], [i], s=52, color=color,
                   marker=COND_MARKER.get(row["set"], "o"), zorder=3)
        ax.annotate(f"{row['convergence_delta']:+.3f}", (max(s, e), i),
                    textcoords="offset points", xytext=(10, -3),
                    fontsize=8, color=INK_2)
    ax.set_yticks(np.arange(len(rows)))
    ax.set_yticklabels([f"{COND_LABEL.get(r['set'], r['set'])}\n{r['model']}"
                        for _, r in rows.iterrows()], fontsize=8, color=INK_2)
    ax.set_xlabel("mean pairwise cosine within condition")
    ax.set_title("Spread of sources (hollow) vs expansions (filled)", loc="left", pad=10)
    ax.xaxis.grid(True)
    ax.set_axisbelow(True)
    ax.margins(x=0.18)
    path = out_dir / "convergence.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def fig_effects(stats, out_dir, plt):
    """Effect sizes with bootstrap CIs -- what D10 says the reader should weigh."""
    import numpy as np

    s = stats[stats["rank_biserial"].notna()].copy()
    if not len(s):
        return None
    models = sorted(s["model"].unique())
    fig, axes = plt.subplots(1, len(models), figsize=(4.6 * len(models), 4.0),
                             squeeze=False, sharex=True)
    for i, model in enumerate(models):
        ax = axes[0][i]
        sub = s[s["model"] == model].iloc[::-1].reset_index(drop=True)
        for y, row in sub.iterrows():
            confirmatory = row.get("role") == "confirmatory"
            color = INK if confirmatory else BLUE
            lo, hi = row["rank_biserial_ci_low"], row["rank_biserial_ci_high"]
            if lo == lo:
                ax.plot([lo, hi], [y, y], color=color, linewidth=2.0, alpha=0.5,
                        solid_capstyle="round", zorder=2)
            ax.scatter([row["rank_biserial"]], [y], s=46 if confirmatory else 34,
                       color=color, marker="D" if confirmatory else "o", zorder=3)
        ax.axvline(0, color=BASELINE, linewidth=1.0, linestyle=(0, (4, 3)), zorder=1)
        ax.set_yticks(np.arange(len(sub)))
        ax.set_yticklabels([f"{r['metric']}{' *' if r.get('role') == 'confirmatory' else ''}"
                            for _, r in sub.iterrows()], fontsize=8, color=INK_2)
        ax.set_title(model, loc="left", pad=10)
        ax.set_xlabel("rank-biserial effect size\n(< 0 = control changes more)")
        ax.xaxis.grid(True)
        ax.set_axisbelow(True)
        ax.set_xlim(-1.05, 1.05)
    fig.suptitle("Effect sizes with 95% bootstrap CIs "
                 "(diamond * = pre-specified confirmatory test)",
                 x=0.02, ha="left", fontsize=10, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path = out_dir / "effect_sizes.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="in_path", required=True, type=Path,
                        help="metrics_<run_id>.csv from metrics.py")
    parser.add_argument("--handcodes", type=Path,
                        help="hand-coding CSV with a filled-in code column")
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()

    import pandas as pd

    plt = _style()
    df = pd.read_csv(args.in_path)
    out_dir = args.out_dir or args.in_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    handcodes = None
    if args.handcodes and args.handcodes.exists():
        hc = pd.read_csv(args.handcodes)
        hc = hc[hc.get("code").astype(str).str.strip() != ""]
        if len(hc):
            pass
            handcodes = hc
            print(f"hand codes: {len(hc)} coded rows")
        else:
            print("hand-coding file has no filled-in codes yet; skipping that panel")

    made = [fig_fidelity(df, out_dir, plt), fig_drift(df, out_dir, plt),
            fig_additions(df, out_dir, plt, handcodes)]

    conv_path = args.in_path.with_name(
        args.in_path.name.replace("metrics_", "convergence_"))
    if conv_path.exists():
        made.append(fig_convergence(pd.read_csv(conv_path), out_dir, plt))

    stats_path = args.in_path.with_name(
        args.in_path.name.replace("metrics_", "paired_stats_"))
    if stats_path.exists():
        made.append(fig_effects(pd.read_csv(stats_path), out_dir, plt))

    for path in made:
        print(f"wrote {path}" if path else "skipped a figure (no data for it)")
    print("captions are RajC's to write")


if __name__ == "__main__":
    main()
