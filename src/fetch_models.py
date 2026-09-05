r"""Pre-download the metric models so a run never stalls on a cold cache.

Fetches config.EMBEDDING_MODEL (D4) and config.NLI_MODEL (D6) into the local
Hugging Face cache and prints the resolved revision of each, so the exact weights
used are recorded in the run snapshot rather than assumed.

CLI: python src\fetch_models.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402


def main() -> None:
    import torch

    print(f"torch {torch.__version__}, cuda available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"device: {torch.cuda.get_device_name(0)}")

    from sentence_transformers import CrossEncoder, SentenceTransformer

    print(f"\nfetching embedding model: {config.EMBEDDING_MODEL}")
    emb = SentenceTransformer(config.EMBEDDING_MODEL)
    dim = emb.get_sentence_embedding_dimension()
    print(f"  ok, embedding dim {dim}, max_seq_length {emb.max_seq_length}")

    print(f"\nfetching NLI model: {config.NLI_MODEL}")
    nli = CrossEncoder(config.NLI_MODEL)
    labels = getattr(nli.model.config, "id2label", None)
    print(f"  ok, labels: {labels}")

    print("\nboth models cached.")


if __name__ == "__main__":
    main()
