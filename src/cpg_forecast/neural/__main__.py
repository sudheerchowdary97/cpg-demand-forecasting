"""CLI for the Task 5 global MLP: train + rolling-origin backtest + leaderboard.

Trains ONE global MLP per fold (`fit_scope="global"`) and scores per market, so
the `mlp` row lands on the same WRMSSE leaderboard as the Task 4 baselines. You
can list reference baselines alongside it for a direct comparison.

Examples:
  # laptop smoke — tiny MLP vs a reference baseline on the sample
  python -m cpg_forecast.neural --sample --models mlp,seasonal_naive --mlflow

  # bigger run, bounded series (prefer cloud GPU for the full dataset)
  python -m cpg_forecast.neural --models mlp --top-series 200 --epochs 60 --mlflow
"""

from __future__ import annotations

import argparse
import logging
import sys

import cpg_forecast.baselines  # noqa: F401  — register the reference baselines
import cpg_forecast.neural  # noqa: F401  — register "mlp"
from cpg_forecast.baselines.base import get
from cpg_forecast.data import DataConfig, generate
from cpg_forecast.eval import (
    BacktestConfig,
    evaluate,
    leaderboard_pivot,
    log_backtest,
    select_top_series,
)
from cpg_forecast.eval.leaderboard import build_leaderboard, write_leaderboard

# LightGBM/XGBoost bundle their own OpenMP runtime, which segfaults when co-loaded
# with torch's in one process on macOS. Compare the MLP against these on Linux/cloud,
# or via a separate `make baselines` run (it writes the same leaderboard file).
_OPENMP_GBMS = {"lightgbm", "xgboost"}

CHECKPOINT_PATH = "models/checkpoints/mlp.ckpt"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(description="Task 5 global MLP — train + backtest.")
    p.add_argument("--models", default="mlp", help="comma-separated: mlp + optional baseline names")
    p.add_argument("--markets", default="all", help="comma-separated markets, or 'all'")
    p.add_argument("--horizon", type=int, default=28)
    p.add_argument("--n-folds", type=int, default=3)
    p.add_argument("--step-days", type=int, default=None)
    p.add_argument("--window", type=int, default=28, help="flattened lookback length L")
    p.add_argument("--epochs", type=int, default=30, help="max training epochs for the MLP")
    p.add_argument("--top-series", type=int, default=None, help="cap to top-N series/market")
    p.add_argument("--sample", action="store_true", help="use the tiny dev dataset")
    p.add_argument("--mlflow", action="store_true", help="log the run to MLflow (./mlruns)")
    p.add_argument(
        "--no-checkpoint", action="store_true", help="skip saving the final MLP checkpoint"
    )
    p.add_argument("--out", default="models/leaderboards", help="leaderboard output directory")
    args = p.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    for name in models:
        get(name)  # validate early with a clear error

    gbms = _OPENMP_GBMS.intersection(models)
    if gbms and sys.platform == "darwin":
        logging.warning(
            "%s + torch in one process segfaults on macOS (dual OpenMP); "
            "run those via `make baselines` or on Linux/cloud. Dropping: %s",
            ",".join(sorted(gbms)),
            ",".join(sorted(gbms)),
        )
        models = [m for m in models if m not in gbms]

    cfg = DataConfig.sample() if args.sample else DataConfig()
    df = generate(cfg)
    if args.markets != "all":
        wanted = {m.strip() for m in args.markets.split(",")}
        df = df[df["market"].isin(wanted)]
    if args.top_series:
        df = select_top_series(df, args.top_series, per_market=True)

    def make_factory(name: str):
        if name == "mlp":
            return lambda: get("mlp")(
                horizon=args.horizon, window=args.window, max_epochs=args.epochs
            )
        return lambda: get(name)(horizon=args.horizon)

    forecasters = {name: make_factory(name) for name in models}
    bt = BacktestConfig(
        horizon=args.horizon, n_folds=args.n_folds, step_days=args.step_days, fit_scope="global"
    )

    logging.info(
        "global backtest: %s on %d rows (%d markets), window=%d",
        ",".join(models),
        len(df),
        df["market"].nunique(),
        args.window,
    )
    results = evaluate(df, forecasters, bt)
    if results.empty:
        logging.warning("no results produced — every model was skipped")
        return

    paths = write_leaderboard(results, out_dir=args.out, stem="task5_leaderboard")
    pivot = leaderboard_pivot(build_leaderboard(results), metric="wrmsse")
    print("\nWRMSSE leaderboard (global fit, per-market score; lower is better):\n")
    print(pivot.round(4).to_string())
    print(f"\nWrote {paths['csv']} and {paths['pivot_csv']}")

    if args.mlflow:
        params = {
            "models": ",".join(models),
            "horizon": args.horizon,
            "n_folds": args.n_folds,
            "window": args.window,
            "epochs": args.epochs,
            "sample": args.sample,
            "top_series": args.top_series,
            "fit_scope": "global",
        }
        log_backtest(results, params, artifacts=paths, run_name="mlp")

    # Train a final MLP on all data and checkpoint it (deployable artifact).
    if "mlp" in models and not args.no_checkpoint:
        logging.info("training final MLP on full data → %s", CHECKPOINT_PATH)
        final = make_factory("mlp")().fit(df)
        final.save_checkpoint(CHECKPOINT_PATH)
        print(f"Saved checkpoint to {CHECKPOINT_PATH}")


if __name__ == "__main__":
    main()
