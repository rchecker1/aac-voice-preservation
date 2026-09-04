# CLAUDE.md — operating rules for this repo

## What this project is

Research project by RajC (sole author) for the joint **Queer in AI × {Dis}ability in AI
workshop at NeurIPS 2026**. Non-archival. **Final submission deadline: Sept 10, 2026 AoE**
(working target: draft complete by ~Sept 7 — see `PLAN.md`).

Research question (RajC's final wording lives in `paper/outline.md`):
when an LLM expands an AAC user's few keywords into a fluent sentence, how much of the
intended meaning and the user's communication style survives — and are autistic
communication styles disproportionately rewritten toward neurotypical norms?

Design: a **systems audit** — measuring models, not people. No human subjects.

Pipeline: source utterance → deterministic keyword compression (simulating telegraphic
AAC input) → LLM expansion → metrics (semantic fidelity, style drift, unlicensed
additions) → analysis, incl. hand-coded sample.

## Non-negotiable rules

The venue requires that generative AI be a supportive tool at most and filters out
AI-generated submissions. Separately, LLM-generated *inputs* would make the study
circular and risk encoding stereotypes of autistic communication. Therefore, in this
repo, Claude must NEVER:

1. **Write, draft, rewrite, or "polish" paper prose.** Everything in `paper/` beyond
   the outline skeleton is authored by RajC. If asked to improve wording there,
   decline and give feedback as comments instead.
2. **Generate, edit, paraphrase, augment, or "fix" any test utterance** in
   `data/suites/`. All items are human-written by RajC. If an item looks
   malformed, flag it in review notes — do not touch the text.
3. **Fabricate or extrapolate results**, example model outputs, or table values.
   Only report numbers that a script in `src/` actually produced.
4. **Make reserved methods decisions unilaterally.** Open decisions live in
   `docs/design_decisions.md`. Implement what's decided; if something is undecided,
   stop and ask RajC.
5. **Scrape or ingest social-media or community content** (Reddit, X/Twitter, forums,
   Discord). Input data comes only from the sources listed in `data/README.md`.

Claude SHOULD, freely: implement pipeline code to spec, debug, write tests, write
plotting code, review methodology and statistics critically, explain concepts, check
reproducibility, and push back when something looks scientifically shaky.

## Environment

- Windows 11 **native** (PowerShell, no WSL); GPU: RTX 5080 (16 GB VRAM, Blackwell —
  PyTorch must be a CUDA 12.8+ build, e.g. the `cu128` wheel index); Python 3.11+;
  venv at `.venv` (activate: `.venv\Scripts\Activate.ps1`; scripts can also be run
  without activation via `.venv\Scripts\python.exe`).
- Paths in commands use Windows separators (`src\compress.py`); code itself uses
  `pathlib`, so `src/` stays portable.
- Local generation through **ollama** for Windows (runs as a background service;
  OpenAI-compatible endpoint `http://localhost:11434/v1`), models under test listed
  in `src/config.py`. Optional API contrast model — RajC decides (D2).
- Embeddings / NLI models via `sentence-transformers` and `transformers` on GPU.

## Conventions

- Small, plain, readable scripts. No frameworks. Artifacts are JSONL/CSV.
- Determinism: fixed seeds everywhere; every run dumps a config snapshot beside its
  outputs in `results/`.
- Language: identity-first ("autistic person"), no functioning labels, no deficit
  framing — in code comments, variable names, and docs, not just the paper.
- Cite sources in `docs/related_work.md`; never invent citations.
