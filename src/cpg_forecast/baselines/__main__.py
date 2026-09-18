"""CLI for the Task 4 local baselines + eval harness.

Runs per-market, rolling-origin backtests for a selected set of baselines and
writes a leaderboard (+ optional MLflow run).

Examples:
  # laptop smoke run — vectorised baselines on the tiny sample
  python -m cpg_forecast.baselines --sample --models simple --mlflow

  # full roadmap set, bounded to the top 200 series/market (heavy → cloud)
  python -m cpg_forecast.baselines --models all --top-series 200
"""

from __future__ import annotations

import argparse
import logging

from cpg_forecast.baselines.base import available, get
from cpg_forecast.data import DataConfig, generate
from cpg_forecast.eval import (
    BacktestConfig,
    evaluate,
    leaderboard_pivot,
    log_backtest,
    select_top_series,
)
from cpg_forecast.eval.leaderboard import build_leaderboard, write_leaderboard

# Convenience groups so `--models simple` expands to the four vectorised ones.
GROUPS = {
    "simple": ["naive", "seasonal_naive", "moving_average", "drift"],
    "statistical": ["ets", "arima", "sarimax", "var"],
    "ml": ["lightgbm", "xgboost"],
    "prophet": ["prophet"],
}


def resolve_models(spec: str) -> list[str]:
    """Expand a --models spec (names, group keywords, or `all`) to real names."""
    if spec.strip() == "all":
        return available()
    names: list[str] = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        names.extend(GROUPS.get(token, [token]))
    for name in names:
        get(name)  # validate; raises KeyError with the available list
    return list(dict.fromkeys(names))  # de-dupe, keep order


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(description="Task 4 local baselines + eval harness.")
    p.add_argument(
        "--models", default="simple", help="names, group (simple/statistical/ml/prophet), or 'all'"
    )
    p.add_argument("--markets", default="all", help="comma-separated markets, or 'all'")
    p.add_argument("--horizon", type=int, default=28)
    p.add_argument("--n-folds", type=int, default=3)
    p.add_argument("--step-days", type=int, default=None)
    p.add_argument(
        "--top-series",
        type=int,
        default=None,
        help="cap to top-N series/market (bounds heavy models)",
    )
    p.add_argument("--sample", action="store_true", help="use the tiny dev dataset")
    p.add_argument("--mlflow", action="store_true", help="log the run to MLflow (./mlruns)")
    p.add_argument("--out", default="models/leaderboards", help="leaderboard output directory")
    args = p.parse_args()

    models = resolve_models(args.models)
    cfg = DataConfig.sample() if args.sample else DataConfig()
    df = generate(cfg)
    if args.markets != "all":
        wanted = {m.strip() for m in args.markets.split(",")}
        df = df[df["market"].isin(wanted)]
    if args.top_series:
        df = select_top_series(df, args.top_series, per_market=True)

    forecasters = {name: (lambda name=name: get(name)(horizon=args.horizon)) for name in models}
    bt = BacktestConfig(horizon=args.horizon, n_folds=args.n_folds, step_days=args.step_days)

    logging.info(
        "running %d baselines on %d rows (%d markets)", len(models), len(df), df["market"].nunique()
    )
    results = evaluate(df, forecasters, bt)
    if results.empty:
        logging.warning("no results produced — every baseline was skipped")
        return

    paths = write_leaderboard(results, out_dir=args.out)
    pivot = leaderboard_pivot(build_leaderboard(results), metric="wrmsse")
    print("\nWRMSSE leaderboard (lower is better, mean over folds):\n")
    print(pivot.round(4).to_string())
    print(f"\nWrote {paths['csv']} and {paths['pivot_csv']}")

    if args.mlflow:
        params = {
            "models": ",".join(models),
            "horizon": args.horizon,
            "n_folds": args.n_folds,
            "sample": args.sample,
            "top_series": args.top_series,
            "markets": args.markets,
        }
        log_backtest(results, params, artifacts=paths)


if __name__ == "__main__":
    main()
