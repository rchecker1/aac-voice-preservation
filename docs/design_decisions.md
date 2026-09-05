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
**DECISION:** embedding cosine with all-mpnet-base-v2 as primary; BERTScore secondary
only if time allows.
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
**DECISION:**
**Rationale:**

## D8 (optional). Suite size + matching
50–100 items per suite; each autistic-style item gets a matched control of similar
length/topic. Decide final N based on writing time on Fri.
**DECISION:**
**Rationale:**
