# Design decisions — RajC decides, code follows

Each decision gets a DECISION line + one-sentence rationale (the rationale goes almost
verbatim into the Methods section, in your words). Claude Code: if any relevant
decision below is blank, stop and ask before implementing.

## D1. Keyword compression rule
Deterministic rule turning a full utterance into telegraphic AAC-style input.
Options: (a) keep content words by POS (NOUN/PROPN/VERB/ADJ/NUM), drop stopwords,
cap at N=3–4 by order of appearance; (b) same but rank by inverse document frequency;
(c) two conditions (N=2 and N=4) to test compression severity.
Tradeoff: (a) is simplest to describe and defend; (c) doubles runs but gives a nice
"more compression → more homogenization?" curve.
**DECISION:** (a) — simple POS content-word rule (keep NOUN/PROPN/VERB/ADJ/NUM, drop
stopwords/auxiliaries), order of appearance, cap N=4 (`MAX_KEYWORDS = 4`). N=2 is a
stretch condition, not planned.
**Rationale:** Appearance order avoids adding judgement.

**D1a. Scope of "drop stopwords" (refinement, decided 2026-09-05).**
The stopword clause applies only to function words, which `KEEP_POS` already excludes
(DET/ADP/PRON/PART/AUX). spaCy's stop list is **not** applied to content words.
Measured on `data/raw/aac_comm/sent_dev_aac.txt` (557 items): applying the stop list to
content words dropped `go`(30), `have`(25), `get`(24), `do`(11), `see`(8), `call`(7),
`give`(7), `take`(6) and excluded 219/557 items (39%) for yielding < 2 keywords;
not applying it excludes 157/557 (28%). It also removed number words (`three`) while
keeping digits (`8`), though both are NUM. Implemented in `compress.py::_keep`;
`compress.py` still reports the affected tokens per run as STOPWORD-DROPPED.
**Rationale:**

**D1b. Politeness markers (decided 2026-09-05).**
`please` is always kept as a keyword regardless of its POS tag (`ALWAYS_KEEP` in
`compress.py`). Measured on `data/raw/aac_comm/sent_train_aac.txt`: `please` occurs in
288/5019 items and spaCy tags it INTJ 261, NOUN 15, VERB 11, ADV 1, AUX 1, so the POS
rule alone kept it 26/289 times (9%) depending on position. Preserving it is what lets
RQ3 separate a politeness marker the user authorised from one the model invented.
Known cost: it consumes one of the four keyword slots. In the toy sentence "Please
tell the nurse my leg hurts." the slot it costs is `hurts`, the predicate. OPEN: should
the MAX_KEYWORDS cap count allowlisted markers, or apply to content words only?
**Rationale:**

**D1b resolved (2026-09-05).** Politeness markers are KEPT and count against the cap.
The alternative (`--strip-register`, remove hedge/politeness terms before the cap) is
implemented and run as an appendix ablation, not as the primary analysis. Keeping them
means nothing is deleted by construction, so the hedge-rate result is empirical rather
than definitional: under strip-register `d_hedge_rate` returns rank-biserial 1.000 with
a zero-width CI, which is the rule restating itself. Primary run: `results/keep_please/`.
Ablation: `results/strip_register/`.
**Rationale:**

**D10 (multiple comparisons and the confirmatory test), settled 2026-09-05.**
Six exploratory tests per model, reported with raw and Holm-adjusted p side by side.
The confirmatory test is the D5 composite, pre-specified and uncorrected. **The primary
composite is the length-adjusted one** (`drift_composite_length_adjusted`): the raw
composite correlates with source length (Spearman 0.59 llama, 0.34 qwen) and control
sources are longer than autistic ones by construction, since hedging is extra words.
Both rows are reported. Under the primary run the adjusted effect is
-0.26 (p = 0.11, llama) and -0.20 (p = 0.22, qwen) -- i.e. no reliable condition
difference in overall drift once length is accounted for.
**Rationale:**

## D2. Models under test
Options: one local quantized ~8B instruct model only; add a second local model;
add one frontier API model for contrast (few dollars).
Tradeoff: two models minimum makes "is this model-specific?" answerable.
**DECISION:** two local models from different families via ollama: `llama3.1:8b` and
`qwen2.5:7b-instruct` (both pulled and endpoint-verified 2026-09-04, ollama 0.33.3).
No API contrast model.
**Rationale:**

## D3. Samples per input (k) and decoding
k=1 greedy vs. k=3 sampled (fixed seeds, temp ~0.7). Sampling shows variance but
triples volume. Compute is cheap either way.
**DECISION:** k=3 sampled, temperature 0.7, fixed seeds (`K_SAMPLES = 3`,
`TEMPERATURE = 0.7`).
**Rationale:**

## D4. Semantic fidelity metric (RQ1)
Sentence-embedding cosine (e.g., all-mpnet-base-v2) as primary; BERTScore as
secondary; report both or one. Keep primary metric singular and defensible.
**DECISION:** embedding cosine with all-mpnet-base-v2 as primary. BERTScore dropped
2026-09-05 (scope cut); the primary metric stands alone.
**Rationale:**

## D5. Style-drift features (RQ2)
Candidate interpretable features: token count ratio, lexical density, hedge-word rate
(from a fixed published hedge lexicon), politeness/softener markers, exclamation rate,
first-person rate, type-token ratio. Plus: embedding distance between expansion and
source *style* (register), and convergence analysis à la Agarwal et al. (pairwise
similarity of expansions within/across conditions). Pick 4–6 features max.
**DECISION:** five features — length ratio, lexical density, hedge rate, first-person
rate, type-token ratio — plus the Agarwal-style convergence analysis.
**Rationale:**
- *Hedge rate:* hedges are exactly what a system adds when it's softening a blunt
  message; if expansions consistently gain hedges the original keywords didn't
  license, that's the model overwriting a direct communication style with a more
  conventionally 'polite' one.
- *Length ratio:* padding terse input takes away its terseness itself: brevity can be
  a stylistic choice, not a deficiency to fix, and a system that reflexively lengthens
  short input is treating economy of expression as something to correct rather than
  preserve.
- *First-person / social-framing rate:* it tracks whether the model is inserting
  relational or affective framing (apologies, softeners, "I just wanted to...") that
  wasn't in the keywords, which is one of the clearest signatures of
  neurotypical-style rewriting.
- *Lexical density:* what's lost when info-dense phrasing flattens is precision:
  literal, information-packed keyword input can get diluted into looser, more
  conversational phrasing, trading exactness for a more "natural-sounding" register.
- *Convergence:* if outputs from stylistically distinct inputs start looking more
  alike than the inputs did, the model isn't expanding each voice on its own terms,
  it's funneling everything toward one default register — evidence of homogenization
  rather than faithful expansion.
- *These five and not others:* each is a documented, citable feature of communication
  style, each is computable from text alone without a model or human judging 'tone',
  and each has a clear predicted direction (up or down) if neurotypical-normalizing
  drift is happening — so the metrics are falsifiable, not just descriptive.

## D6. Unlicensed-additions detection (RQ3)
NLI-based flag: expansion clauses not entailed by source utterance (model:
nli-deberta-v3-base) → export flagged + random sample for hand-coding.
Alternative: keyword-overlap heuristic (weaker). Hand-coding is the ground truth
either way; automatic flags just prioritize.
**DECISION:** NLI flags with nli-deberta-v3-base to prioritize; RajC's hand-coding is
the ground truth.
**Rationale:**

## D7. Hand-coding rubric (RQ3 ground truth)
Draft categories to refine: (1) faithful expansion, (2) benign filler (politeness
padding), (3) new factual content, (4) stance/tone change (e.g., hedged, softened,
made "nicer"), (5) meaning reversal. Code 100–200 items; report per-category rates
by condition. You write the rubric and do all coding.
**DECISION:** five ordered categories, treated as a ladder of increasing severity:
(1) faithful expansion → (2) benign filler → (3) unlicensed new content →
(4) tone/stance shift → (5) meaning reversal. Frozen before any coding begins.
**Rationale:**
- *Why the categories run faithful → filler → unlicensed content → tone shift →
  reversal:* it's a ladder, not a flat list, because each step is a strictly worse
  failure mode in terms of fidelity to intent: filler is harmless noise, unlicensed
  content adds meaning that wasn't there, tone shift changes how the message lands
  without changing its content, and reversal actually inverts the speaker's intent —
  ordering them lets you report not just how often the system fails but how badly.
- *Why the tone-shift category matters most:* this is the thesis: it's the category
  where the words are technically 'right' but the register has been quietly rewritten
  toward neurotypical norms, and because nothing is factually wrong, this is exactly
  the failure mode a purely semantic-similarity or accuracy metric would miss
  entirely.
- *Why the rubric is frozen before coding:* it prevents you from unconsciously
  adjusting category boundaries once you've seen which examples look bad, which would
  let your hypothesis (autistic-style inputs drift more) shape the very labels meant
  to test it.

## D8 (optional). Suite size + matching
50–100 items per suite; each autistic-style item gets a matched control of similar
length/topic. Decide final N based on writing time on Fri.
**DECISION:** 50 matched pairs (`aut-NNN` / `ctl-NNN`). Revised down from 100 on
2026-09-05 to protect the writing days (PLAN.md standing rule: cut scope, not
writing). 50 pairs still supports the paired test at a medium effect size.
Matching holds topic and approximate length constant; communication style is the
variable. Analysis is therefore paired: Wilcoxon signed-rank on within-pair
differences. Working practice: write each pair together and never leave one half
finished, so the suites stay balanced and analyzable if writing stops early.
Cost check: 100 items x 2 models x k=3 = 600 generations, ~10 min locally, $0.
**Rationale:**

## D15. Locus split for rung-3 `tone_shift` (required analysis)
The symmetric removal rule is near-deterministic on condition given this
compressor: autistic sources carry ~no mitigation (1/50), control sources all
do, so removal-direction `tone_shift` can fire only on control. The
by-condition tone_shift rate is therefore partly a property of the rubric x
suite interaction, and reporting it raw would be circular.
**DECISION:** report `tone_shift` split by locus, computed automatically from
src/exp hedge rates and keyword hedge content:
- mitigation cut by the compressor, never seen by the model;
- mitigation surviving into keywords, dropped by the model;
- (for additions) mitigation absent from keywords, introduced by the model.
Current numbers (2026-09-07 run): 120 control generations lost mitigation --
96 compressor-cut, 24 model-dropped; where mitigation survived compression
(n = 162) the model preserved it 85% of the time. Same shape as the
keep-negation result (polarity restored 96/96 once keywords carried it).
**The finding this licenses:** the bottleneck destroys stance and polarity;
the models mostly transmit what they are given.
