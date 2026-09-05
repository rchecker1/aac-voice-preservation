# Feature sources

Every item in the autistic-style suite is tagged with one or more of four
features. This file gives the citation basis for each tag: what the claimed
feature is, what supports it, and how confident that support is.

**Scope caveat, stated up front.** These citations establish that each feature
is *documented as more common in autistic communication*. They do not establish
that any feature is universal, diagnostic, or exclusive to autistic people.
Autism is heterogeneous and none of these apply to all autistic communicators
(Reframing Autism, 2025; National Autistic Society, n.d.). The suite is a
constructed probe for a documented style cluster, not a model of autistic
people. This is the limitation already stated in the paper.

---

## `direct`

**Claim.** A preference for saying the intended message explicitly, without
mitigating or indirect framing; sometimes read by non-autistic listeners as
bluntness.

**Support — strong.**

- Crompton, C. J., et al. (2025). Information transfer within and between
  autistic and non-autistic people. *Nature Human Behaviour*. Registered
  Report. States that autistic people often communicate in a more direct,
  literal or frank manner, which non-autistic listeners sometimes read as rude
  but which autistic listeners prefer.
- Milton, D. E. M. (2012). On the ontological status of autism: the "double
  empathy problem." *Disability & Society*, 27(6), 883-887. Frames the
  mismatch as bidirectional rather than as an autistic deficit — the
  theoretical basis for treating directness as a *style*, not an error to be
  corrected. This is the load-bearing citation for the whole paper.
- Crompton, C. J., Ropar, D., Evans-Williams, C. V., Flynn, E. G., &
  Fletcher-Watson, S. (2020). Autistic peer-to-peer information transfer is
  highly effective. *Autism*, 24(7), 1704-1712. Direct style is not a
  transmission failure: autistic-to-autistic transfer is as efficient as
  non-autistic-to-non-autistic.
- Heasman, B., & Gillespie, A. (2019). Neurodivergent intersubjectivity.
  *Autism*, 23(4), 910-921. Describes low-inference, explicit interactional
  norms among autistic interlocutors.
- Sasson, N. J., et al. (2017). Neurotypical peers are less willing to
  interact with those with autism based on thin slice judgments. *Scientific
  Reports*, 7, 40700. Establishes that the *reception* penalty is real, which
  is why an AAC system trained on neurotypical text has an incentive to
  normalise this feature away.

---

## `literal`

**Claim.** Language is produced and interpreted at face value; the surface
content is the content.

**Support — strong.**

- Happé, F. G. E. (1993). Communicative competence and theory of mind in
  autism: A test of relevance theory. *Cognition*, 48(2), 101-119.
- Norbury, C. F. (2005). The relationship between theory of mind and metaphor:
  Evidence from children with language impairment and autistic spectrum
  disorder. *British Journal of Developmental Psychology*, 23(3), 383-399.
- Williams, G. L., Wharton, T., & Jagoe, C. (2021). Mutual (mis)understanding:
  Reframing autistic pragmatic "impairments" using relevance theory.
  *Frontiers in Psychology*, 12, 616664. Reframes literalness as a coherent
  pragmatic strategy rather than a deficit — use this rather than the older
  deficit-framed sources where you can.
- Kalandadze, T., Norbury, C., Nærland, T., & Næss, K. B. (2018). Figurative
  language comprehension in individuals with autism spectrum disorder: A
  meta-analytic review. *Autism*, 22(2), 99-117. Meta-analytic, so the
  strongest single citation for this tag.

---

## `info_dense`

**Claim.** High ratio of propositional content to total words; specifics
(numbers, times, names) stated rather than approximated; low tolerance for
phatic padding.

**Support — moderate. Read the caveat.**

- Heasman, B., & Gillespie, A. (2019), above. Documents information-focused
  interactional norms.
- Dunn, K., et al. (2023), as summarised in Reframing Autism (2025),
  *Autistic Communication Differences: A Primer*. Autistic people tend to
  value direct information-sharing over social-norm-driven small talk.
- Grice, H. P. (1975). Logic and conversation. In Cole & Morgan (Eds.),
  *Syntax and Semantics 3*. Not an autism source — cited because several
  papers characterise autistic conversational style as more strictly
  Gricean (informative, non-redundant), which is the mechanism behind this
  tag.

**Caveat.** "Information density" as an operationalised, measured construct in
autistic speech is thinner in the peer-reviewed literature than `direct` or
`literal`. The term "infodumping" is widely used in autistic community writing
but is community-attested rather than empirically quantified. Do not overclaim
this tag in the paper — describe it as a documented tendency, and note that
your lexical-density metric is measuring the constructed suite, not a validated
population norm.

---

## `low_hedging`

**Claim.** Reduced use of epistemic softeners, mitigators, and politeness
downgraders relative to matched neurotypical phrasing.

**Support — weakest of the four. Flag this in the paper.**

- Brown, P., & Levinson, S. C. (1987). *Politeness: Some Universals in
  Language Usage*. Cambridge UP. Establishes hedging/mitigation as the core
  negative-politeness machinery — the thing that is absent.
- Holmes, J. (1984). Modifying illocutionary force. *Journal of Pragmatics*,
  8(3), 345-365. Establishes hedges as attenuators of illocutionary force,
  which is what makes their *addition* by an expansion model a change of
  speaker stance and not a neutral fluency edit.
- Milton (2012) and Crompton et al. (2025), above. Low hedging is best treated
  as a **corollary of `direct`** rather than an independently evidenced
  feature: the directness literature describes unmitigated phrasing, and
  mitigation is what hedges do.

**Honest position for the write-up.** There is no study I can cite that
directly measures hedge frequency in autistic vs. non-autistic speech with a
published lexicon. Say so. Frame `low_hedging` as an operationalisation of the
well-evidenced `direct` feature, chosen because it is computable, rather than
as a separately attested finding. A reviewer who knows this literature will
notice if you claim otherwise, and the concession costs you nothing.

---

## `scripted` — dropped

Declared in `data/README.md` but used by zero items. Two options:

1. **Drop it.** Remove the declaration from `README.md`. Recommended — an
   unused tag in a released artifact reads as an abandoned condition and
   invites a reviewer question you gain nothing by answering.
2. **Keep it noted.** If you intend to add scripted/formulaic-language items
   in the follow-up, leave the declaration but add: `# declared for v2; no
   items in v1`. Supporting citation if you do:
   Prizant, B. M. (1983). Language acquisition and communicative behavior in
   autism: Toward an understanding of the "whole" of it. *Journal of Speech
   and Hearing Disorders*, 48(3), 296-307 (delayed echolalia / formulaic
   speech); Dobbinson, S., Perkins, M., & Boucher, J. (2003). The interactional
   significance of formulas in autistic language. *Clinical Linguistics &
   Phonetics*, 17(4-5), 299-307.

Default to option 1 unless v2 is already scoped.

---

## Verification note

These references are given from a literature that I know well, but I have not
opened each one to confirm volume, issue, and page numbers in this session.
Before submission, verify every entry against the publisher record — especially
the Crompton et al. (2025) *Nature Human Behaviour* Registered Report, which is
recent enough that pagination may differ from what is listed here.
