# Design decisions — addendum D11–D14

Drafted for RajC to adopt or overrule. These four were decided *after* seeing
results, so unlike D1–D10 they cannot claim pre-specification — each rationale
says what the decision protects instead.

---

**D11 — Source length is confounded with condition. Decision: (a).**
Report raw and length-adjusted, adjusted as primary, and declare the confound
constitutive rather than accidental: hedging *is* added words, so a
length-matched control suite would have to strip hedges or pad the autistic
items — either of which destroys the style contrast the suite exists to carry —
and adjusting for length while stating plainly that length and register are
entangled is the honest version of a separation the data cannot give you.
(b) is out on time and would be wrong anyway; (c) throws away a real analysis
to avoid writing one limitation paragraph.

**D12 — d_hedge_rate floors in the autistic condition. Decision: (a).**
Keep it in the composite and publish the sensitivity table, because the
composite was pre-specified and dropping a component after seeing that removal
flips one model to n.s. is exactly the garden-of-forking-paths move D10 exists
to forbid — the floor (49/50 autistic sources at hedge_rate 0) is not a bug in
the metric but a description of the construct, since a feature defined by
absence can only move in one direction from zero, and the sensitivity table
lets the reader see precisely how much of the result that one-sidedness
carries.

**D13 — Framing after a null confirmatory result. Decision: (a), with the null
stated first, not buried.**
The pre-registered composite test is null and is reported as null in the
abstract — then the paper leads with what the hand codes and polarity split
actually show, clearly labelled exploratory: the dominant failure mode of the
keyword bottleneck is not register drift but *intent reversal*, concentrated
almost entirely on negation-carrying sources (75% of negated sources coded
reversal vs 5% otherwise), and the sign of the drift runs opposite to the
hypothesis — hedged control inputs degrade *more*, because hedge tokens that
survive into the keyword window get confabulated as propositional content
("mind" → "hurt my mind", "free" → "for free", "think" → "need to think
about"). A null on the hypothesis plus a mechanism you can name is a better
paper than a rescued p-value, and this venue in particular will trust the
first and punish the second.

**D14 — Is the polarity loss an artifact of the D1 rule? Decision: (a).**
Run --keep-negation and report both arms, because the question "does the
finding survive when negation is preserved?" is answerable for one GPU-hour and
a reviewer will ask it in the first round; if reversal collapses under
keep-negation, the finding is correctly restated as "AAC keyword schemes that
drop negation cause intent reversal, and LLM expansion does not repair it" —
which is still a publishable, actionable claim about deployed systems, since
stripping function words (negation included) is what real keyword-based AAC
front-ends do. Framing it as compression-scheme-only *without* running the
ablation (option b) would leave the paper asserting an attribution it never
tested.

---

## Consequences for the write-up

1. RQ2's confirmatory status ends at the null. Everything downstream of the
   hand codes is exploratory and is labelled so every time it is mentioned.
2. The thesis sentence changes. Old: "expansion rewrites autistic style toward
   neurotypical norms." New: "the keyword bottleneck destroys polarity and
   stance for everyone, hedged style most of all, and expansion reconstructs a
   plausible-sounding intent the speaker never had." The smoke-test example
   ("please pass the water" → "I need to pass water") is still the paper in
   one line — it was never a style finding, it was a reversal finding.
3. The safety claim gets sharper, not weaker: reversal is a worse failure for
   an AAC user than register drift, because the device says the *opposite* of
   the intended message in the user's voice, and the user may not be able to
   repair it quickly.
