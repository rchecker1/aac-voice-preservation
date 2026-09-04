"""Expansion generation: keywords -> model expansions, fully logged.

Spec:
- Read compressed JSONL; for each record x each model in config.MODELS x k in
  range(K_SAMPLES): call the model with prompts/expand.txt filled in.
- ollama backend via its OpenAI-compatible endpoint (config.OLLAMA_BASE_URL) using
  the `openai` client; optional API backend added only if D2 says so.
- Seeded where the backend supports it; retries with backoff on connection errors;
  strip whitespace/quotes from outputs; refuse-to-answer outputs kept verbatim and
  flagged `refusal_like: true` (they are data — see Rizvi et al.'s failure modes).
- Output: results/expansions_<run_id>.jsonl with model, sample_idx, seed, expansion,
  latency; dump a config snapshot results/config_<run_id>.json alongside.
- --smoke flag: run 5 items x 1 model x k=1 end to end.

CLI: python src/generate.py --in results/compressed_all.jsonl
"""

# TODO(claude-code): implement per spec above once D2/D3 are decided.
