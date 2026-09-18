"""MLflow experiment tracking for the eval harness (Task 4).

A thin, optional wrapper: if mlflow isn't installed (or logging fails) the run
degrades to a no-op with a warning, so tracking is never a hard dependency of
scoring. Uses a local file store (`./mlruns`, git-ignored) — no server needed;
browse with `mlflow ui`. Task 11 promotes this to full experiment management.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_EXPERIMENT = "task4_baselines"
DEFAULT_TRACKING_URI = "file:./mlruns"


def _metric_key(model: str, market: str, metric: str) -> str:
    # MLflow metric keys allow [A-Za-z0-9_/.- ]; markets/metrics are already safe.
    return f"{model}.{market}.{metric}"


def log_backtest(
    results: pd.DataFrame,
    params: dict,
    artifacts: dict[str, Path] | None = None,
    experiment: str = DEFAULT_EXPERIMENT,
    tracking_uri: str = DEFAULT_TRACKING_URI,
    run_name: str = "baselines",
) -> None:
    """Log one run: params, per-(model,market) mean metrics, and artifact files.

    Everything is logged under a single run so the leaderboard and its inputs
    stay together; per-series detail is intentionally omitted (that's Task 11).
    """
    try:
        import mlflow
    except ImportError:
        logger.warning("mlflow not installed — skipping tracking (pip install '.[baselines]')")
        return

    # MLflow 3.x deprecated the plain file store; opt back in (Task 11 moves to a
    # proper backend). Also silence the per-run agent hint so logs stay readable.
    os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
    os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

    try:
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment)
        with mlflow.start_run(run_name=run_name):
            mlflow.log_params({k: str(v) for k, v in params.items()})
            if not results.empty:
                agg = results.groupby(["model", "market", "metric"])["value"].mean()
                metrics = {
                    _metric_key(model, market, metric): float(value)
                    for (model, market, metric), value in agg.items()
                    if pd.notna(value)
                }
                mlflow.log_metrics(metrics)
            for path in (artifacts or {}).values():
                if Path(path).exists():
                    mlflow.log_artifact(str(path))
    except Exception as exc:  # noqa: BLE001 — tracking must never break scoring
        logger.warning("mlflow logging failed (%s) — continuing without tracking", exc)
