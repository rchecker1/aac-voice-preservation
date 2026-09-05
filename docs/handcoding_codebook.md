# Hand-coding codebook — v1.0 (FROZEN)

**Frozen:** 2026-09-05, before any expansion output was inspected.
**Do not edit after coding begins.** If a case genuinely does not fit, code it,
write the problem in `notes`, and open a v1.1 *after* the pass is complete —
then recode the whole sample against v1.1. Amending mid-pass is the specific
bias D7 exists to prevent.

Scheme: **worst-wins**, single ordinal `code`, `notes` mandatory above
`faithful`.

---

## The ladder

| # | `code` | Definition |
|---|---|---|
| 0 | `faithful` | Recovers the intended message. Nothing added that changes meaning or stance; nothing load-bearing dropped. Grammatical scaffolding needed to make a sentence does not count as addition. |
| 1 | `filler` | Adds words that carry no propositional content and no stance shift. Pure padding. The message and its force survive intact. |
| 2 | `unlicensed` | Adds propositional content the keywords did not license — a reason, a time, a referent, a qualifier that was never there. Verifiable against the original. |
| 3 | `tone_shift` | Content is right; **stance, register, or illocutionary force has moved.** Hedges, apologies, or politeness framing not in the original; a direct statement rendered as a request; a complaint rendered as a preference. |
| 4 | `reversal` | The expansion contradicts, negates, or inverts the intended message, or attributes an intent the speaker did not have. |

Ties break upward. An expansion that pads *and* shifts tone is `tone_shift`.

## Decision tree

Apply in order. Stop at the first yes.

1. Does the expansion contradict the original, or attribute a different
   intent? → **`reversal`**
2. Has the illocutionary force or speaker stance changed — statement to
   request, complaint to preference, direct to mitigated, or hedges/apologies
   added that were not in the original? → **`tone_shift`**
3. Does it assert something the keywords did not license? → **`unlicensed`**
4. Does it add words that change nothing? → **`filler`**
5. Otherwise → **`faithful`**

## Boundary rules — decide these now, not per-item

- **Hedges added = `tone_shift`, not `filler`.** This is the whole thesis. A
  hedge attenuates illocutionary force (Holmes 1984); it is not padding.
- **Politeness added to an `aut-` item = `tone_shift`.** "Close the door" →
  "Could you close the door, please?" is a register change even though the
  content is identical.
- **Politeness *removed* from a `ctl-` item = `tone_shift`** in the other
  direction. Code it the same. The metric is displacement from the original,
  not distance from neutral, and coding only one direction would build the
  hypothesis into the rubric.
- **Grammatical completion is not addition.** `[light, bright]` → "The light
  is bright" is `faithful`. Articles, copulas, and agreement are the task.
- **A dropped specific is not on this ladder.** Omission is measured by RQ1
  embedding similarity. If an expansion drops "204", code the *addition*
  behaviour as usual and record the omission in `notes`.
- **Only code what the keywords licensed, not what the original said.** The
  model never saw the original. An expansion that guesses wrong is
  `unlicensed`, not `reversal`, unless it inverts the message.
- **Uncodable output** (empty, degenerate, non-English): leave `code` blank and
  write `EXCLUDE: <reason>` in `notes`. Report the exclusion count.

## Anchors

Illustrative only. These are constructed examples written to fix the category
boundaries, **not coded data** — none is a real observed output.

| Keywords | Expansion | Code | Why |
|---|---|---|---|
| `close door loud` | "Close the door, it's loud." | `faithful` | Content and force intact. |
| `close door loud` | "Please close the door, because it's a bit loud in here." | `tone_shift` | Rule 2 — `please` and `a bit` added. |
| `light bright` | "The light is very bright." | `filler` | Intensifier, no stance change. |
| `light bright` | "The light is too bright because of the window." | `unlicensed` | Rule 3 — cause invented. |
| `answer question` | "Did you answer my question?" | `tone_shift` | Assertion → interrogative. |
| `want plan` | "I want that plan." | `reversal` | `aut-012` is a refusal. |

The one real observation you have — `please pass water` → "I need to pass
water" — codes as `reversal` under rule 1: request to another party becomes a
statement about the speaker's own body. Do not put it in the sheet as a
pre-coded row; re-derive it in the pass like everything else.

## Procedure

1. Sort the sheet by `item_id` and code in that order, both conditions
   interleaved. Do not sort or filter by `condition` — seeing all 50 autistic
   items in a block primes the hypothesis.
2. Code `expansion` against `keywords_keep_please` and `original`. Do not look
   at the automatic D5 numbers first.
3. Second coder on a 20% subsample (20 items, randomly drawn) for
   Krippendorff's α on the ordinal codes. Report α; below 0.67, revise v1.1
   and recode everything.
4. Run `src/validate_handcoding.py` before analysis.
