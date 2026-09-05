r"""Orchestrator: validate -> compress -> generate -> metrics -> figures, one command.

Every stage is still runnable on its own; this just chains them with a shared run_id
so one run's artifacts land together and can be traced back to a config snapshot.

  python src\run_pipeline.py --smoke    # 5 items, 1 model, k=1, sanity check
  python src\run_pipeline.py --full     # everything, seeded, snapshotted

Stage 0 refuses to continue if validate_suites.py reports an ERROR, so a malformed
suite cannot silently become a result. Warnings are printed and do not block.

Everything for run <id> goes to results/<id>/:
  inputs.jsonl  compressed.jsonl  expansions_<id>.jsonl  config_<id>.json
  metrics_<id>.csv  paired_stats_<id>.csv  convergence_<id>.csv
  handcode_sample_<id>.csv  and the four PNGs
Figure captions and interpretation are RajC's, not generated.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

SRC = Path(__file__).resolve().parent
PY = sys.executable


def run_stage(name: str, argv: list[str], allow_fail: bool = False) -> int:
    print(f"\n=== {name} " + "=" * max(0, 62 - len(name)))
    proc = subprocess.run([PY, *argv])
    if proc.returncode and not allow_fail:
        raise SystemExit(f"\nstage '{name}' failed (exit {proc.returncode}); stopping")
    return proc.returncode


def collect_suites(out_path: Path, suites_dir: Path) -> tuple[int, list[str]]:
    """Concatenate the suite files into one JSONL the pipeline reads."""
    paths = sorted(suites_dir.glob("*.jsonl"))
    if not paths:
        raise SystemExit(
            f"no suite files in {suites_dir}.\n"
            "The suites are hand-written by RajC (see data/README.md); the pipeline "
            "has nothing to run until they exist."
        )
    n = 0
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as fh:
        for path in paths:
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    fh.write(line.strip() + "\n")
                    n += 1
    return n, [p.name for p in paths]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--smoke", action="store_true",
                      help="5 items x 1 model x k=1")
    mode.add_argument("--full", action="store_true", help="the real run")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--handcodes", type=Path,
                        help="a filled-in hand-coding CSV, for the D7 figure panel")
    parser.add_argument("--skip-validation", action="store_true",
                        help="do not gate on validate_suites.py (not for the real run)")
    parser.add_argument("--suites-dir", type=Path, default=config.DATA_SUITES,
                        help="where the suite JSONL files live (default data/suites); "
                             "override only for rehearsals against fixture data")
    args = parser.parse_args()

    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = config.RESULTS / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"run_id {run_id}\nout_dir {out_dir}\nmode {'smoke' if args.smoke else 'full'}")

    if not args.skip_validation:
        rc = 0
        for suite in sorted(args.suites_dir.glob("*.jsonl")):
            rc |= run_stage(f"0. validate {suite.name}",
                            [str(SRC / "validate_suites.py"), "--in", str(suite)],
                            allow_fail=True)
        if rc:
            raise SystemExit("\nsuite validation reported ERRORs; fix them and re-run "
                             "(or pass --skip-validation to override deliberately)")

    inputs = out_dir / "inputs.jsonl"
    n_items, names = collect_suites(inputs, args.suites_dir)
    print(f"\ncollected {n_items} items from {', '.join(names)} -> {inputs}")

    compressed = out_dir / "compressed.jsonl"
    run_stage("1. compress", [
        str(SRC / "compress.py"), "--in", str(inputs), "--out", str(compressed),
        "--report", str(out_dir / f"compress_report_{run_id}.json"),
    ])

    gen_argv = [str(SRC / "generate.py"), "--in", str(compressed),
                "--out-dir", str(out_dir), "--run-id", run_id]
    if args.smoke:
        gen_argv.append("--smoke")
    run_stage("2. generate", gen_argv)

    expansions = out_dir / f"expansions_{run_id}.jsonl"
    run_stage("3. metrics", [
        str(SRC / "metrics.py"), "--in", str(expansions), "--out-dir", str(out_dir),
    ])

    fig_argv = [str(SRC / "figures.py"), "--in", str(out_dir / f"metrics_{run_id}.csv"),
                "--out-dir", str(out_dir)]
    if args.handcodes:
        fig_argv += ["--handcodes", str(args.handcodes)]
    run_stage("4. figures", fig_argv)

    manifest = {
        "run_id": run_id,
        "mode": "smoke" if args.smoke else "full",
        "suite_files": names,
        "n_input_items": n_items,
        "artifacts": sorted(p.name for p in out_dir.iterdir()),
    }
    (out_dir / f"manifest_{run_id}.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\n=== done " + "=" * 62)
    print(f"{len(manifest['artifacts'])} artifacts in {out_dir}")
    print("every number in the paper should be traceable to a file in there")


if __name__ == "__main__":
    main()
