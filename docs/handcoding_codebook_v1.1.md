# Hand-coding codebook — v1.1 (DRAFT — freeze before recoding begins)

Opened 2026-09-07, after completion of the v1.0 pass, per the v1.0 amendment
rule. **The whole 96-item sample is recoded against this version. The
reliability coder codes their rows against this version, fresh.** v1.0 codes
are retained in the repo for the audit trail but are not analysed.

This document is coder-facing. It names no item from either suite, and every
example in it is constructed on content that appears in neither suite. The
mapping between rule changes and the specific items that motivated them lives
in `docs/coding_audit_trail.md`, which the reliability coder must not read
before coding.

## Changelog from v1.0

1. **Ladder rung 3 restated as explicitly bidirectional.** v1.0 defined the
   rung by additions only and left the removal direction in a boundary rule,
   which the pass under-applied. The rung definition now carries both
   directions itself.
2. **Possessive-determiner rule added.** "Grammatical completion" in v1.0
   named articles, copulas, and agreement; possessives were a gap.
3. **Reversal vs unlicensed boundary sharpened:** reversal requires the
   intended message to be contradicted, inverted, or displaced entirely. If
   the original proposition survives — even demoted to a subordinate clause —
   and new content is added around it, that is `unlicensed`.
4. **Internal contradiction removed:** the v1.0 `faithful` definition
   required "nothing load-bearing dropped" while the omission boundary rule
   put drops off-ladder. The definition no longer mentions omission.
5. **An example of unverified provenance was removed** and replaced with
   constructed anchors.

No other rule changed: the decision tree order, worst-wins, mandatory notes,
EXCLUDE, and interleaving are as in v1.0.

---

## The ladder

| # | `code` | Definition |
|---|---|---|
| 0 | `faithful` | Recovers the intended message. Nothing added that changes meaning or stance. Grammatical scaffolding needed to make a sentence does not count as addition. (Omissions are off-ladder; see boundary rules.) |
| 1 | `filler` | Adds words that carry no propositional content and no stance shift. Pure padding. The message and its force survive intact. |
| 2 | `unlicensed` | Adds propositional content the keywords did not license — a reason, a time, a referent, a party, a qualifier that was never there — while the original message still survives in the expansion. |
| 3 | `tone_shift` | Content is right; **stance, register, or illocutionary force has moved in either direction.** Hedges, apologies, or politeness present in the original and absent from the expansion, or absent from the original and present in the expansion; a direct statement rendered as a request, or a mitigated request rendered as a demand. |
| 4 | `reversal` | The expansion contradicts, negates, or inverts the intended message, or replaces it: the speaker's intent is displaced such that the original message no longer survives as an assertion of the expansion. |

Ties break upward. An expansion that pads *and* shifts tone is `tone_shift`.

## Decision tree

Apply in order. Stop at the first yes.

1. Does the expansion contradict or invert the original, or displace its
   message entirely (the original proposition no longer asserted)? →
   **`reversal`**
2. Has illocutionary force or speaker stance moved, in either direction —
   mitigation added where the original had none, or mitigation present in the
   original missing from the expansion? → **`tone_shift`**
3. Does it assert something the keywords did not license, with the original
   message still present? → **`unlicensed`**
4. Does it add words that change nothing? → **`filler`**
5. Otherwise → **`faithful`**

## Boundary rules

- **Hedges or politeness added = `tone_shift`, not `filler`.** A hedge
  attenuates illocutionary force (Holmes 1984); it is not padding.
- **Hedges or politeness removed = `tone_shift`, symmetrically.** The metric
  is displacement from the original, not distance from neutral. This applies
  regardless of where the loss originated — if mitigation was cut upstream
  and the expansion did not restore it, the displacement is still coded;
  locus of fault is an analysis question, not a coding question.
- **Grammatical completion is not addition.** Articles, copulas, agreement,
  and the first-person singular possessive `my` on a referent the speaker
  can naturally own are scaffolding: an AAC utterance is first-person by
  default and `my` commits the speaker to nothing new.
- **Any determiner that introduces a party beyond the speaker is not
  scaffolding.** `our`, `your`, `his`, `her`, `their` assert other people's
  involvement the keywords never licensed → `unlicensed`, or higher if the
  tree says so.
- **The reversal/unlicensed line runs through survival of the message.** If
  the original proposition is still asserted somewhere in the expansion,
  the ceiling for added content is `unlicensed`; if the speaker's intent has
  been replaced, it is `reversal`.
- **A dropped specific is off-ladder.** Omission is measured elsewhere. Code
  the addition/stance behaviour as usual and record the omission in `notes`.
- **Worst-wins sets the code; `notes` carries the rest.** When one expansion
  both shifts stance and adds unlicensed content, code the higher rung and
  name the lower-rung behaviour in `notes` — it must not be lost.
- **Only code what the keywords licensed, not what the original said** —
  except the symmetric tone rule, where displacement is defined against the
  original by construction.
- **Uncodable output** (empty, degenerate, non-English): leave `code` blank,
  write `EXCLUDE: <reason>` in `notes`, report the count.

## Anchors

Constructed examples only; the content below appears in neither suite and in
no coded item.

| Keywords | Original | Expansion | Code | Why |
|---|---|---|---|---|
| `feed cat 7` | Feed the cat at 7. | "Feed the cat at 7." | `faithful` | Content and force intact. |
| `grass wet slippery` | The grass is wet. It's slippery. | "Careful, the grass might be a bit wet and slippery." | `tone_shift` | Mitigation added to a direct warning. |
| `lock gate dog gets` | Sorry, could you lock the gate? The dog gets out. | "Lock the gate. The dog gets out." | `tone_shift` | Mitigation stripped upstream, not restored — same rung, other direction. |
| `train platform 4` | The train is on platform 4. | "The train is right there on platform 4." | `filler` | Padding, no stance change. |
| `train platform 4` | The train is on platform 4. | "The train is on platform 4 because of engineering works." | `unlicensed` | Cause invented; message survives. |
| `bike tire flat` | The bike tire is flat. | "Our bike tire is flat." | `unlicensed` | Determiner adds a party. |
| `trust weather forecast` | I don't trust the weather forecast. | "I trust the weather forecast." | `reversal` | Polarity inverted. |
| `carry box heavy` | Carry this box for me. It's heavy. | "I'll carry the box for you, it's heavy." | `reversal` | Roles inverted; the request no longer survives. |

## Procedure

Unchanged from v1.0: interleave by `item_id`, never sort by condition; code
against keywords and original before looking at any automatic numbers;
reliability coder on randomly drawn rows for Krippendorff's α (target ≥ 0.67;
below it, revise and recode). Validate with `src/validate_handcoding.py`
before analysis.

For the recode specifically: **recode in a freshly shuffled interleaved
order, and do not consult the v1.0 codes or any by-condition tallies while
coding.** Apply the rules row by row and let the distribution land where it
lands.
