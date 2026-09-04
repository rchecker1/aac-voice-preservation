"""Orchestrator: compress -> generate -> metrics -> figures, one command.

CLI:
  python src/run_pipeline.py --smoke    # 5 items, 1 model, sanity check
  python src/run_pipeline.py --full     # everything, seeded, snapshotted

Each stage writes to results/<run_id>/ ; run_id = UTC timestamp. The figures stage
produces: fidelity_by_condition.png, drift_by_condition.png, additions_rates.png,
convergence.png — captions/interpretation are written by RajC, not generated.
"""

# TODO(claude-code): wire the stages together after individual modules pass their tests.
