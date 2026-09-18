"""Reusable evaluation harness (Task 4).

Metrics (WRMSSE + supporting), rolling-origin backtesting, per-market
leaderboards, and optional MLflow tracking. Kept separate from `baselines/`
because every later model (Tasks 5–12) scores through this same module.
"""

from cpg_forecast.eval.backtest import (
    BacktestConfig,
    Forecaster,
    evaluate,
    select_top_series,
)
from cpg_forecast.eval.leaderboard import (
    build_leaderboard,
    leaderboard_pivot,
    write_leaderboard,
)
from cpg_forecast.eval.tracking import log_backtest

__all__ = [
    "BacktestConfig",
    "Forecaster",
    "evaluate",
    "select_top_series",
    "build_leaderboard",
    "leaderboard_pivot",
    "write_leaderboard",
    "log_backtest",
]
