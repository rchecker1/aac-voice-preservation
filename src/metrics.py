"""Metrics for RQ1 (fidelity), RQ2 (style drift), RQ3 (unlicensed additions).

RQ1 — semantic fidelity (D4):
- cosine(source_embedding, expansion_embedding) with config.EMBEDDING_MODEL.
- Optional secondary: BERTScore. Report per-condition distributions, not just means.

RQ2 — style drift (D5):
- Interpretable feature deltas between expansion and source: token-count ratio,
  lexical density, hedge-rate (fixed lexicon file src/hedges.txt — RajC curates the
  list from a published hedge lexicon and cites it), first-person rate,
  exclamation rate, type-token ratio. Pick the 4-6 features D5 selects.
- Convergence analysis (Agarwal et al.-style): pairwise similarity among expansions
  within condition vs. among sources within condition. If expansions are more
  similar to each other than sources were, that's homogenization.
- Key contrast: drift(autistic_style) vs. drift(control_style) on matched items;
  paired stats (Wilcoxon), effect sizes, not just p-values.

RQ3 — unlicensed additions (D6):
- NLI with config.NLI_MODEL: split expansion into clauses; flag clauses not entailed
  by the source utterance; rate per condition.
- Export a stratified random sample of config.HANDCODE_SAMPLE_SIZE expansions to
  results/handcode_sample.csv with empty rubric columns (D7). RajC codes by hand;
  compute agreement between NLI flags and hand codes.

All outputs: tidy CSVs in results/ that pandas + matplotlib scripts can plot directly.
No number reaches the paper unless it comes from these files.
"""

# TODO(claude-code): implement per spec above once D4-D7 are decided.
