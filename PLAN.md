# PLAN.md — Sept 4 → Sept 10 (AoE)

Hard deadline: **Wed Sept 10 AoE**. Working target: **full draft by ~Sun Sept 7**,
so the 8th–9th are buffer, not plan.

Legend: **[YOU]** = RajC only (the parts that make the work yours and keep it valid).
**[CC]** = do it with Claude Code. Timebox everything; scope creep is the enemy.

## Thu Sept 4 — lock the design (today)
- [ ] **[YOU]** Rewrite the RQ in your own words in `paper/outline.md`.
- [ ] **[YOU]** Make decisions D1–D7 in `docs/design_decisions.md` (with rationale).
- [x] **[CC]** Set up venv, ollama, pull the chosen models, smoke-test generation.
- [x] **[CC]** Implement `compress.py` per D1 and unit-test it on 10 toy sentences.
- [ ] **[YOU]** Locate + download the neutral AAC-like phrase set (see `data/README.md`);
      record license/terms in `data/raw/SOURCES.md`.

## Fri Sept 5 — data day
- [ ] **[YOU]** Write the autistic-style suite + matched control suite (50–100 items
      each), feature-tagged, each tag grounded in a citation. This is the single most
      important human task in the project. No AI involvement, none.
- [x] **[CC]** Validation script: schema check, length stats, tag counts.
      (`srcalidate_suites.py` — run it as you write; it also previews which items
      compress.py would exclude.)
- [x] **[CC]** `generate.py`: expansions for all inputs × models × k samples, seeded,
      logged to `results/`. Smoke-tested on both D2 models; same seed reproduces
      byte-identical output.

## Sat Sept 6 — run everything + human judgment
- [x] **[CC]** `metrics.py`: fidelity, style-drift features, NLI additions flags.
- [ ] **[YOU]** Spot-check 20 outputs by eye before trusting any number.
- [ ] **[YOU]** Write the additions coding rubric (D7) and hand-code the sampled
      100–200 expansion items exported by `metrics.py`.
- [x] **[CC]** Figures: fidelity distributions; drift by condition; additions rates.
      (`srcigures.py`; `srcun_pipeline.py --full` chains every stage. Rehearsed
      end to end on fixture data: 100 items -> 600 generations -> 4 figures in ~1 min.)
- [ ] **[YOU]** Write down, in plain sentences, what the results actually show.

## Sun Sept 7 — write (target: full draft tonight)
- [ ] **[YOU]** Draft Methods and Results while everything is fresh.
- [ ] **[CC]** Regenerate any figure that needs fixing; double-check every number
      in the draft against `results/` files.
- [ ] **[YOU]** Intro, related work (you've read `docs/related_work.md` sources),
      limitations (constructed suites; no autistic collaborators yet; call for
      co-design validation), positionality note if you choose to include one.
- [ ] **[CC]** Reference formatting, LaTeX/template mechanics only.

## Mon Sept 8 – Tue Sept 9 — buffer + polish
- [ ] **[YOU]** Full read-aloud pass; ask one human to skim it.
- [ ] Anything that slipped from Sept 4–7 lands here — cut scope, don't cut writing.

## Wed Sept 10 — submit
- [ ] **[YOU]** Check the venue's formatting/submission requirements and submit
      with hours to spare, not minutes. AoE buys you time — don't spend it all.

## Standing rules
- If a day slips, cut scope (fewer models, fewer metrics), never the writing days.
- Any number in the paper must be reproducible by one command from `results/` inputs.
