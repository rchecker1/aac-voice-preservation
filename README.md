# Whose Sentence Is It? — voice preservation in LLM keyword-to-sentence expansion for AAC

Working title. Submission target: **Queer in AI × {Dis}ability in AI workshop @ NeurIPS 2026**
(non-archival; extended abstract / work-in-progress). **Deadline: Sept 10, 2026 AoE.**

## The question

AAC (augmentative and alternative communication) users often enter a few keywords and
let software produce the full sentence. Prior work evaluates these systems on **speed**
(keystroke savings, WPM). This project evaluates them on **voice**:

1. **Meaning (RQ1).** Round-trip fidelity: original utterance → keyword compression →
   LLM expansion → how close is the expansion to the original?
2. **Style (RQ2).** Drift: do expansions preserve the source's register (length,
   directness, hedging, phrasing) or converge on generic LLM register — and is drift
   larger for autistic-style inputs than matched neurotypical-style inputs?
3. **Additions (RQ3).** How often does the model insert meaning the keywords never
   licensed ("unlicensed additions") — the measurable version of putting words in
   someone's mouth?

It's a systems audit: we measure **models**, not people. No human subjects.

## Repo map

- `CLAUDE.md` — rules for Claude Code sessions in this repo. Read it first.
- `PLAN.md` — day-by-day schedule to the deadline, with human-only tasks marked.
- `docs/design_decisions.md` — open methods decisions (RajC decides, then code follows).
- `docs/related_work.md` — reading list + positioning notes.
- `data/README.md` — data sources, suite-construction protocol, schema, prohibitions.
- `src/` — pipeline: `compress.py` → `generate.py` → `metrics.py` → `run_pipeline.py`.
- `prompts/` — the expansion prompt(s) under test.
- `paper/outline.md` — section skeleton. Prose is written by RajC only.
- `results/` — run outputs (JSONL/CSV + config snapshots + figures).

## Quickstart (Windows 11 native, PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
# PyTorch FIRST, from the CUDA 12.8 wheel index — the RTX 5080 (Blackwell) needs it;
# plain `pip install torch` gives a build without sm_120 support.
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
python -m spacy download en_core_web_sm
# local model server: install ollama for Windows (runs as a background service), then:
#   ollama pull <each model in src/config.py MODELS>
python src\run_pipeline.py --smoke   # tiny end-to-end test once data exists
```

## Status

- [ ] Decisions D1–D7 made (`docs/design_decisions.md`)
- [ ] Neutral AAC-like set acquired (`data/raw/`)
- [ ] Style suites written by RajC (`data/suites/`)
- [ ] Pipeline runs end to end
- [ ] Metrics + figures
- [ ] Hand-coded additions sample
- [ ] Draft complete
- [ ] Submitted
