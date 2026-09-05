# Citation verification log

Status of every reference in `data/suites/feature_sources.md`, which states that its
entries were not checked against publisher records when written. Checked 2026-09-05
against publisher/PubMed records.

Two separate questions per entry:
1. **Exists?** Are the authors, title, venue, year, volume and pages right?
2. **Supports?** Does the paper actually say the thing it is cited for?

A citation can pass (1) and fail (2). Three below do.

---

## Verified — bibliographic details correct

| Citation | Record |
|---|---|
| Crompton et al. (2025), *Nature Human Behaviour* | Real. Registered Report, July 2025. DOI 10.1038/s41562-025-02163-z |
| Crompton, Ropar, Evans-Williams, Flynn & Fletcher-Watson (2020), *Autism* 24(7), 1704–1712 | Real. DOI 10.1177/1362361320919286, PMID 32431157 |
| Heasman & Gillespie (2019), *Autism* 23(4), 910–921 | Real. DOI 10.1177/1362361318785172, PMID 30073872 |
| Williams, Wharton & Jagoe (2021), *Frontiers in Psychology* 12, 616664 | Real. DOI 10.3389/fpsyg.2021.616664, PMID 33995177 |
| Kalandadze, Norbury, Nærland & Næss (2018), *Autism* 22(2), 99–117 | Real. DOI 10.1177/1362361316668652, PMID 27899711 |
| Sasson et al. (2017), *Scientific Reports* 7, 40700 | Real. DOI 10.1038/srep40700, PMID 28145411 |

## Claim-attachment problems — real paper, questionable support

**Crompton et al. (2025) — cited as the primary support for `direct`.**
`feature_sources.md` says it "states that autistic people often communicate in a more
direct, literal or frank manner, which non-autistic listeners sometimes read as rude
but which autistic listeners prefer." The paper is a diffusion-chain study of 311
participants reporting that autistic and non-autistic people transfer information
comparably well, that rapport is higher within matched neurotypes, and that disclosure
of diagnostic status improves rapport. That supports the double-empathy framing; it is
not a finding about directness being read as rude. **Either locate the passage that
makes the directness claim, or re-attach the claim to a source that does.** This is the
load-bearing citation for the `direct` tag.

**Heasman & Gillespie (2019) — cited for `direct` and again for `info_dense`.**
Cited as describing "low-inference, explicit interactional norms." The paper's two
reported features are a *generous assumption of common ground* and a *low demand for
coordination*, observed during collaborative video gaming. Assuming common ground is
close to the opposite of low-inference explicitness, so the wording needs checking
against the text. The `info_dense` use ("documents information-focused interactional
norms") is a further stretch from what the study measured.

**Kalandadze et al. (2018) — cited as the strongest single source for `literal`.**
The meta-analysis does report poorer figurative-language comprehension (Hedges'
g = −0.57), but reports that the difference is **non-significant when groups are
matched on verbal ability**. Citing it without that caveat overstates it, and it is
deficit-framed — which `feature_sources.md` itself advises against preferring.

## Not verified

- **Dunn, K., et al. (2023)** — cited only "as summarised in Reframing Autism (2025)",
  with no title. Uncheckable as written. Supply the title or drop it; it is one of only
  three sources under `info_dense`, the tag the file already flags as weakest-evidenced.
- Milton (2012); Happé (1993); Norbury (2005); Prizant (1983); Dobbinson, Perkins &
  Boucher (2003) — well-known works, not individually checked here. Low risk of not
  existing, but volume/page details are unconfirmed.
- `src/hedges.txt` sources — Hyland (1998, 2005); Holmes (1984, 1990); Lakoff (1973);
  Brown & Levinson (1987). All are standard works, but the separate question is whether
  the **lexicon entries actually come from those lists**. Nothing has been checked
  against Hyland's appendix. Section 7 of the file already flags its own entries as
  extensions; sections 1–6 are the ones that carry the attribution.
- Reframing Autism (2025); National Autistic Society (n.d.) — web sources, not checked.

## Note on the lexicon, from the run rather than the literature

`feel` is listed as an epistemic hedge (§2). In `aut-048` / `ctl-048` ("I feel
overwhelmed right now") it is the content verb, not a hedge, and stripping it drops the
pair from the analysis entirely. Hedge lexicons built from academic prose mis-fire on
first-person emotional statements, which are common in AAC. Worth one sentence in the
limitations, and worth deciding whether to exclude `feel` from the lexicon.
