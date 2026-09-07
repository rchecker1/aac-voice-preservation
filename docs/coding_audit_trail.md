# Coding audit trail — NOT coder-facing

**The reliability coder must not read this file before coding.** It exists so
that every v1.1 rule change is traceable to the observations that motivated
it, and so the provenance of the calibration pass is on the record.

## Calibration provenance

The file `data/coding/handcode_keep_please_claude_calibration.csv` was
produced by an LLM (Claude, in the planning conversation of 2026-09-07), coding
19 real pipeline expansions against codebook v1.0. **It is not a second coder
and is excluded from all reliability statistics.** Its sole use was locating
rubric ambiguity before the reliability pass: exact agreement with the v1.0
human codes was 11/19, and the disagreement pattern exposed the directional
under-application of the hedge-removal rule that v1.1 changelog item 1 fixes.
The model also authored codebook v1.0 and drafted v1.1, which is a further
reason its codes cannot serve as independent judgment. Machine-vs-human
agreement is reported in the paper only via the NLI-vs-hand-code comparison
(κ = 0.65), labelled as automatic triage.

## Item mappings behind the v1.1 changes

- **Changelog 1 (bidirectional rung 3):** ctl-032, ctl-026 (coded `faithful`
  in v1.0 despite lost mitigation), ctl-001, ctl-010, aut-042 (coded
  `unlicensed`/`faithful` where stance had moved). Five of eight calibration
  disagreements were this one error, all in the direction that undercounts
  control-side failures.
- **Changelog 2 (possessive determiners):** aut-013 ("My report") — `my`
  ruled scaffolding; aut-024 ("Our flight") — `our` adds a party, recodes
  from `faithful` to `unlicensed` under the new rule.
- **Changelog 3 (reversal/unlicensed line):** ctl-013 ("I need to think
  about my report, which is due on Friday") — proposition survives demoted,
  so `unlicensed`, settling the calibration disagreement in favour of the
  v1.0 human code; aut-019 ("I'll give you a blanket because you have a
  cold") — intent replaced, `reversal`.
- **Changelog 5 (removed example):** "please pass the water" → "I need to
  pass water" originated in an informal pre-pipeline session, is not present
  in `results/`, and is not citable unless reproduced under the pipeline
  with a run ID.

## Anchor replacement record

Four v1.1-draft anchors were real sample items (ctl-001, aut-019, aut-030,
aut-012), and the draft prose named aut-013 and aut-024 — with ctl-001,
aut-019, aut-013, and aut-024 all present in the 19-row reliability sample,
this pre-answered ~4 of 18 unique items. All eight anchors were replaced on
2026-09-07 with constructed content verified (word-boundary grep) to appear
in neither suite. Any future anchor must pass the same check before the
codebook is frozen.

## Locus split — required analysis for rung 3 (D15)

The symmetric removal rule is near-deterministic on condition given this
compressor: autistic sources carry ~no mitigation (1/50), control sources all
do, so removal-direction `tone_shift` can fire only on control. The
by-condition tone_shift rate is therefore partly a property of the rubric ×
suite interaction, and reporting it raw would be circular.

Required: report `tone_shift` split by locus, computed automatically from
src/exp hedge rates and keyword hedge content:

- mitigation cut by the compressor, never seen by the model;
- mitigation surviving into keywords, dropped by the model;
- (for additions) mitigation absent from keywords, introduced by the model.

Current numbers (2026-09-07 run): 120 control generations lost mitigation —
96 compressor-cut, 24 model-dropped; where mitigation survived compression
(n = 162) the model preserved it 85% of the time. Same shape as the
keep-negation result (polarity restored 96/96 once keywords carried it). The
finding this licenses: the bottleneck destroys stance and polarity; the
models mostly transmit what they are given. Write D15 into
`docs/design_decisions.md` in this form.
