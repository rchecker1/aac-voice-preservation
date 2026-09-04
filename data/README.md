# Data — sources, construction protocol, schema

## Hard rules (repeat of CLAUDE.md, because they matter most here)
- No AI-generated, AI-edited, or AI-paraphrased input utterances. Ever. LLM-authored
  inputs make the study circular and risk encoding stereotypes.
- No scraping of community spaces (Reddit, X, forums, Discord).
- Every source's license/terms recorded in `data/raw/SOURCES.md`.

## Set 1 — neutral AAC-like phrases (`data/raw/`)
Primary: the crowdsourced AAC-like phrase collection from Vertanen & Kristensson
(EMNLP 2011) — check the authors' data pages (Keith Vertanen hosts AAC research
datasets) and the paper for access; widely used in AAC text-entry research.
Fallback: short conversational utterances (≤ 15 words) filtered from a
research-licensed dialogue corpus (e.g., DailyDialog) — note the license.
Target: 100–200 utterances after filtering. Claude Code may write download/filter
scripts but RajC verifies the source and terms.

## Set 2 — style suites (`data/suites/`) — HUMAN-WRITTEN ONLY
Two matched suites written by RajC, 50–100 items each:

- `autistic_style.jsonl` — items exhibiting communication features documented in
  peer-reviewed literature and published first-person accounts by autistic writers.
  Candidate feature tags (each must carry a citation in `data/suites/feature_sources.md`
  before use): `direct` (explicit, unsoftened requests/statements), `literal`,
  `info_dense` (detailed special-interest sharing), `scripted` (formulaic/echolalic
  phrasing), `low_hedging` (minimal softeners/small talk).
- `control_style.jsonl` — matched neurotypical-register counterparts: similar topic
  and length, conventional hedging/softening/small-talk patterns.

Construction protocol: for each item, write the full utterance yourself, tag its
features, note the source grounding the feature (not the sentence — sentences are
yours). Aim for everyday communicative contexts an AAC user might type (requests,
plans, opinions, sharing info), varied topics, 5–20 words.

Validity note for the paper's limitations: these are constructed suites, not
naturalistic autistic discourse, and no autistic collaborators reviewed them yet —
say this plainly and call for co-design validation as the next step.

## Schema (all input files, JSONL)
```json
{"id": "aut-014", "set": "autistic_style", "style_tags": ["direct", "info_dense"],
 "text": "…", "topic": "plans", "source_note": "feature grounding ref"}
```
Pipeline adds: `keywords` (from compress.py), then per-expansion records in
`results/` with `model`, `seed`, `sample_idx`, `expansion`, and metric columns.
