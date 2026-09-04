"""Deterministic keyword compression: full utterance -> telegraphic AAC-style input.

Spec (finalize via D1 before implementing):
- spaCy en_core_web_sm; keep tokens whose POS is in config.KEEP_POS, excluding
  auxiliaries and stopwords; preserve order of appearance; cap at config.MAX_KEYWORDS.
- Lowercase keywords; keep numbers as digits.
- Must be a pure function: same input -> same output, no randomness.
- Edge cases: utterances yielding < 2 keywords are logged and excluded (report count).

CLI: python src/compress.py --in data/suites/autistic_style.jsonl \
        --out results/compressed_autistic_style.jsonl
Adds a "keywords" field to each record.

Include a __main__ self-test on ~10 hardcoded toy sentences with expected outputs
(RajC signs off on the expected outputs — they document the rule for the paper).
"""

# TODO(claude-code): implement per spec above once D1 is decided.


def compress(text: str, max_keywords: int) -> list[str]:
    raise NotImplementedError
