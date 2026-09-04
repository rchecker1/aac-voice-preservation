"""Central configuration. Values marked DECIDE come from docs/design_decisions.md."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_SUITES = ROOT / "data" / "suites"
RESULTS = ROOT / "results"
PROMPT_FILE = ROOT / "prompts" / "expand.txt"

SEED = 3501

# --- Generation (D2, D3) ---
OLLAMA_BASE_URL = "http://localhost:11434/v1"
MODELS = [
    # D2: two local models, different families. Pulled + verified against the
    # endpoint 2026-09-04 (ollama 0.33.3).
    {"name": "llama3.1:8b", "backend": "ollama"},
    {"name": "qwen2.5:7b-instruct", "backend": "ollama"},
]
K_SAMPLES = 3          # D3: sampled
TEMPERATURE = 0.7      # D3: fixed seeds per sample (see generate.py)
MAX_TOKENS = 64

# --- Compression (D1) ---
KEEP_POS = {"NOUN", "PROPN", "VERB", "ADJ", "NUM"}  # D1: confirmed
MAX_KEYWORDS = 4       # D1: cap, order of appearance; N=2 is a stretch condition only

# --- Metrics (D4, D5, D6) ---
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"  # D4: primary metric
NLI_MODEL = "cross-encoder/nli-deberta-v3-base"              # D6: flags only; hand-coding is ground truth
STYLE_FEATURES = [  # D5: plus Agarwal-style convergence analysis (metrics.py)
    "length_ratio",
    "lexical_density",
    "hedge_rate",
    "first_person_rate",
    "type_token_ratio",
]
HANDCODE_SAMPLE_SIZE = 150  # items exported for RajC's hand-coding (D7)
