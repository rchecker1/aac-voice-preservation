# data/raw/ — sources, terms, verification status

## Crowdsourced AAC-like communications corpus (`aac_comm/`)

- **Downloaded:** 2026-09-04, from https://www.aactext.org/imagine/ (file `aac_comm.zip`),
  by Claude Code at RajC's direction.
- **What it is:** ~6,000 fictional AAC-like communications invented by Amazon Mechanical
  Turk workers imagining use of a scanning-style AAC interface (see bundled
  `aac_comm/readme.txt`). Line counts as downloaded: `sent_train_aac.txt` 5,019;
  `sent_dev_aac.txt` 557; `sent_test_aac.txt` 566. Original worker case/punctuation kept.

### Citation (as requested on the source page)

> Keith Vertanen and Per Ola Kristensson. The Imagination of Crowds: Conversational
> AAC Language Modeling using Crowdsourcing and Large Data Sources. In *Proceedings
> of the Conference on Empirical Methods in Natural Language Processing (EMNLP)*.
> ACL: 700–711, 2011.

### Terms as stated on the source page (retrieved 2026-09-04)

- The page states the materials are licensed under **Creative Commons CC BY 4.0**
  (attribution required), **except** `lm_test_switch.txt` and `lm_test_comm.txt`,
  which the page says carry separate restrictions (they derive from Switchboard and
  from data originally collected by H. Venkatagiri, and required special permission
  from the original sources).

### ⚠️ For RajC to verify personally (per data/README.md hard rules)

1. **Confirm the CC BY 4.0 statement on the live page yourself** — the bundled
   `readme.txt` inside the zip does *not* contain any license text; the licensing
   statement exists only on the web page, so eyeball it before the paper claims it.
2. **The zip includes the two restricted files** (`lm_test_switch.txt`,
   `lm_test_comm.txt`). Recommendation: exclude both from the study set entirely and
   rely only on `sent_*_aac.txt`. Confirm, and confirm they need no further action.
3. **Provenance caveat for the paper:** these are *fictional* communications imagined
   by crowdworkers, not utterances produced by AAC users — a limitation the paper
   should state alongside the constructed-suites caveat.
4. Files not downloaded: the ARPA language models and word lists linked from the page
   (not needed for this study; `vocab_aac_twitter.txt` and `american_words.txt` came
   inside the zip but are unused).

## Not present here

`data/suites/` content is human-written by RajC only — see `data/README.md`. Nothing
in `data/raw/` may be AI-generated, AI-edited, or scraped from community spaces.
