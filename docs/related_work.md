# Related work — reading list + positioning

RajC: read every "core" paper before writing the related-work section. Add your own
notes under each. Claude Code: never invent citations; if a detail is uncertain,
mark it TODO-verify.

## Core — must cite and position against

1. **Rizvi et al. 2026** — "Algorithmic Fragility and Persona Bias in LLM-Generated
   Autistic Communication." arXiv:2605.26397. Ten LLMs rewrite naturally occurring
   autistic discourse under autistic vs. neurotypical personas; autistic-persona
   rewrites diverge more in lexical form and affective register at equivalent semantic
   similarity; failure modes include erasure and stereotyped hallucination.
   **Position:** closest prior work; rewrite setting, not the AAC keyword bottleneck.
   Motivates our hypothesis. Our claim must be scoped to the AAC expansion setting.
   - notes:

2. **Shen et al. 2022 (KWickChat)** — IUI 2022. Keyword→sentence generation for AAC;
   evaluated with BLEU/WER/embedding similarity to a target reply, keystroke savings,
   and human judges on semantic consistency. **Position:** the meaning-recovery
   machinery exists but is aimed at utility, not voice/style; generic dialogue data.
   - notes:

3. **Cai et al. 2024 (SpeakFaster)** — Nature Communications. LLM abbreviation
   expansion accelerating eye-gaze typing for users with ALS. **Position:** the
   flagship speed result; our work adds the missing evaluation axis.
   - notes:

4. **Valencia et al. 2023** — CHI. "The less I type, the better": how AI language
   models can enhance or impede communication for AAC users. **Position:** the
   qualitative agency concern we operationalize.
   - notes:

5. **Weinberg et al. 2026** — CHI. "I, Robot? Exploring Ultra-Personalized AI-Powered
   AAC" (autoethnography). Personalized model amplified/muted aspects of the author's
   identity. **Position:** qualitative, n=1; we quantify at system level.
   - notes:

6. **Agarwal, Naaman & Vashistha 2025** — CHI. "AI Suggestions Homogenize Writing
   Toward Western Styles..." arXiv:2409.11360. Embedding-similarity convergence method
   for homogenization, cultural axis. **Position:** methodological template; we
   transpose the homogenization question to neurodivergence in AAC.
   - notes:

7. **Martin & Nagalakshmi 2025 ("Aging Up AAC")** — arXiv:2404.17730. Interviews with
   12 autistic adults; autistic adults neglected in AAC design; LLM features added
   without user perspectives. **Position:** motivation for centering autistic AAC users.
   - notes:

## Supporting

8. **Xu et al. 2025 (Speak Ease)** — arXiv:2503.17479. Expressivity-focused LLM AAC,
   evaluated via SLP focus groups. Solutions-side; we're measurement-side.
9. **Vertanen & Kristensson 2011** — EMNLP. Crowdsourced AAC-like phrase collection —
   candidate neutral input set (see data/README.md).
10. **Gaines & Vertanen 2025** — arXiv:2501.10582. LLMs for character-based AAC;
    useful background on AAC input-rate constraints (~5–10 WPM).

## Framing / language (read before writing anything)

11. **Keyes 2020** — "Automating Autism." The canonical critique of detection-framed
    autism AI; explains why this project is deliberately not a classifier.
12. **Bottema-Beutel et al. 2021** — "Avoiding Ableist Language." Follow it everywhere.

## Novelty claim (to verify, then state in RajC's own words)

To our knowledge: first quantitative evaluation of meaning + style preservation through
the AAC keyword-compression→expansion bottleneck; first differential test of autistic
vs. matched neurotypical styles in that setting; first unlicensed-additions rate as an
agency metric. Verify before claiming: Scholar "cited by" on #1–#4; arXiv full-text
search for AAC + style/voice preservation; ASSETS 2026 accepted titles.
