r"""Expansion generation: keywords -> model expansions, fully logged.

Implements D2 (two local models via ollama) and D3 (k=3 sampled, temperature 0.7,
fixed seeds). Every run writes two files into results/:
  expansions_<run_id>.jsonl   one record per (item x model x sample)
  config_<run_id>.json        snapshot of every setting that shaped the run

The prompt in prompts/expand.txt is part of the system under test and is copied
verbatim into the snapshot. Model outputs are never edited: `expansion_raw` is exactly
what came back, `expansion` is the same string with surrounding whitespace and paired
quotes stripped. Refusal-shaped outputs are kept as data and flagged `refusal_like`.

CLI:
  python src\generate.py --in results\compressed_all.jsonl
  python src\generate.py --in results\compressed_all.jsonl --smoke
  python src\generate.py --in ... --models llama3.1:8b --limit 20
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

# D1 output is a keyword list; how it is rendered into the prompt is visible to the
# model, so it is a named setting, logged in every config snapshot. Space-joined
# matches how telegraphic AAC input actually reaches a composition feature.
KEYWORD_JOIN = " "

MAX_RETRIES = 4
RETRY_BACKOFF_S = 2.0

# Refusal markers, deliberately narrow: phrases in which the model talks about ITSELF
# declining the task, not ordinary first-person sentences. An earlier, looser list
# flagged "I love you, but I'm not able to feed you right now, I'm truly sorry" as a
# refusal -- a faithful expansion of the keywords love/sorry/able/feed. Because
# metrics.py drops refusal_like rows from the paired statistics by default, such false
# positives would preferentially delete apologetic, softened expansions, which is a
# bias aimed straight at the hypothesis under test.
REFUSAL_MARKERS = (
    "as an ai", "as a language model", "i cannot assist", "i can't assist",
    "cannot help with that", "can't help with that", "i cannot provide",
    "i can't provide", "i cannot fulfill", "i can't fulfill", "i cannot generate",
    "i can't generate", "i cannot comply", "i'm not able to help",
    "i am not able to help", "i cannot create", "i can't create",
)

# Second gate: a genuine refusal ignores the user's words. If most of the keywords
# survive into the output, it is an expansion, whatever phrases it happens to contain.
REFUSAL_KEYWORD_COVERAGE = 0.5


def keyword_coverage(text: str, keywords: list[str]) -> float:
    """Share of keywords that appear in the output (prefix match, case-insensitive)."""
    if not keywords:
        return 0.0
    low = text.lower()
    hits = sum(1 for k in keywords if k.lower()[:4] in low)
    return hits / len(keywords)


def run_id_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_prompt_template() -> str:
    """prompts/expand.txt minus its leading comment block."""
    lines = config.PROMPT_FILE.read_text(encoding="utf-8").splitlines()
    body = [ln for ln in lines if not ln.lstrip().startswith("#")]
    return "\n".join(body).strip()


def build_prompt(template: str, keywords: list[str]) -> str:
    return template.replace("{keywords}", KEYWORD_JOIN.join(keywords))


def clean_output(text: str) -> str:
    """Strip whitespace and one layer of paired surrounding quotes. No other edits."""
    out = text.strip()
    while len(out) >= 2 and out[0] == out[-1] and out[0] in "\"'“‘":
        out = out[1:-1].strip()
    if len(out) >= 2 and out[0] in "“‘" and out[-1] in "”’":
        out = out[1:-1].strip()
    return out


def looks_like_refusal(text: str, keywords: list[str]) -> bool:
    """Meta-refusal phrasing AND the user's keywords largely absent."""
    low = text.strip().lower()
    if not any(m in low for m in REFUSAL_MARKERS):
        return False
    return keyword_coverage(text, keywords) < REFUSAL_KEYWORD_COVERAGE


def seed_for(sample_idx: int) -> int:
    """Deterministic per-sample seed (D3: fixed seeds)."""
    return config.SEED + sample_idx


def _client():
    from openai import OpenAI

    # ollama ignores the key but the client requires a non-empty one.
    return OpenAI(base_url=config.OLLAMA_BASE_URL, api_key="ollama")


def call_model(client, model: str, prompt: str, seed: int) -> tuple[str, float]:
    """One generation. Retries connection/transient errors with backoff."""
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            t0 = time.perf_counter()
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS,
                seed=seed,
            )
            latency = time.perf_counter() - t0
            return resp.choices[0].message.content or "", latency
        except Exception as exc:  # noqa: BLE001 - retry anything the backend throws
            last_exc = exc
            if attempt == MAX_RETRIES - 1:
                break
            wait = RETRY_BACKOFF_S * (2 ** attempt)
            print(f"    retry {attempt + 1}/{MAX_RETRIES - 1} after {type(exc).__name__}"
                  f" ({exc}); sleeping {wait:.0f}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"{model}: generation failed after {MAX_RETRIES} attempts") from last_exc


def _git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=config.ROOT,
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def config_snapshot(in_path: Path, models: list[dict], k: int, run_id: str,
                    template: str) -> dict:
    return {
        "run_id": run_id,
        "input": str(in_path),
        "git_commit": _git_commit(),
        "python": sys.version,
        "platform": platform.platform(),
        "prompt_file": str(config.PROMPT_FILE),
        "prompt_template": template,
        "keyword_join": KEYWORD_JOIN,
        "models": models,
        "k_samples": k,
        "temperature": config.TEMPERATURE,
        "max_tokens": config.MAX_TOKENS,
        "seed_base": config.SEED,
        "seeds": [seed_for(i) for i in range(k)],
        "ollama_base_url": config.OLLAMA_BASE_URL,
        "max_keywords": config.MAX_KEYWORDS,
        "keep_pos": sorted(config.KEEP_POS),
    }


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{lineno}: invalid JSON ({exc})")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="in_path", required=True, type=Path,
                        help="compressed JSONL from compress.py")
    parser.add_argument("--out-dir", type=Path, default=config.RESULTS)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--models", nargs="*", default=None,
                        help="subset of config.MODELS names")
    parser.add_argument("--limit", type=int, default=None, help="first N items only")
    parser.add_argument("--smoke", action="store_true",
                        help="5 items x first model x k=1")
    args = parser.parse_args()

    records = read_jsonl(args.in_path)
    models = config.MODELS
    if args.models:
        wanted = set(args.models)
        models = [m for m in config.MODELS if m["name"] in wanted]
        missing = wanted - {m["name"] for m in models}
        if missing:
            raise SystemExit(f"unknown model(s): {', '.join(sorted(missing))}")
    k = config.K_SAMPLES

    if args.smoke:
        records, models, k = records[:5], models[:1], 1
    elif args.limit:
        records = records[: args.limit]

    missing_kw = [str(r.get("id", "?")) for r in records if not r.get("keywords")]
    if missing_kw:
        raise SystemExit(f"{args.in_path}: {len(missing_kw)} record(s) have no "
                         f"keywords (run compress.py first): {', '.join(missing_kw[:5])}")

    run_id = args.run_id or run_id_now()
    template = load_prompt_template()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / f"expansions_{run_id}.jsonl"
    snap_path = args.out_dir / f"config_{run_id}.json"

    snap = config_snapshot(args.in_path, models, k, run_id, template)
    snap_path.write_text(json.dumps(snap, indent=2), encoding="utf-8")

    total = len(records) * len(models) * k
    print(f"run_id {run_id}: {len(records)} items x {len(models)} model(s) x k={k} "
          f"= {total} generations")
    print(f"  -> {out_path}\n  -> {snap_path}")

    from tqdm import tqdm

    client = _client()
    n_refusal = 0
    t_start = time.perf_counter()
    with out_path.open("w", encoding="utf-8", newline="\n") as fh:
        with tqdm(total=total, unit="gen") as bar:
            for model in models:
                for rec in records:
                    prompt = build_prompt(template, rec["keywords"])
                    for sample_idx in range(k):
                        seed = seed_for(sample_idx)
                        raw, latency = call_model(client, model["name"], prompt, seed)
                        expansion = clean_output(raw)
                        refusal = looks_like_refusal(expansion, rec["keywords"])
                        coverage = keyword_coverage(expansion, rec["keywords"])
                        n_refusal += refusal
                        fh.write(json.dumps({
                            "run_id": run_id,
                            "id": rec.get("id"),
                            "set": rec.get("set"),
                            "style_tags": rec.get("style_tags"),
                            "topic": rec.get("topic"),
                            "source_text": rec.get("text"),
                            "keywords": rec["keywords"],
                            "prompt": prompt,
                            "model": model["name"],
                            "backend": model.get("backend"),
                            "sample_idx": sample_idx,
                            "seed": seed,
                            "temperature": config.TEMPERATURE,
                            "expansion": expansion,
                            "expansion_raw": raw,
                            "refusal_like": refusal,
                            "keyword_coverage": round(coverage, 3),
                            "latency_s": round(latency, 3),
                        }, ensure_ascii=False) + "\n")
                        fh.flush()
                        bar.update(1)

    elapsed = time.perf_counter() - t_start
    print(f"done: {total} generations in {elapsed:.1f}s "
          f"({elapsed / max(total, 1):.2f}s each), refusal_like: {n_refusal}")


if __name__ == "__main__":
    main()
