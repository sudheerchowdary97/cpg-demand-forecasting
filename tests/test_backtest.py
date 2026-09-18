"""Tests for the Task 4 backtest harness + leaderboard."""

from __future__ import annotations

import pandas as pd

from cpg_forecast.baselines import get
from cpg_forecast.data import DataConfig, generate
from cpg_forecast.eval import BacktestConfig, evaluate, select_top_series
from cpg_forecast.eval.leaderboard import build_leaderboard, leaderboard_pivot


def _sample() -> pd.DataFrame:
    return generate(DataConfig.sample())


def _simple_forecasters():
    return {name: (lambda name=name: get(name)()) for name in ("naive", "seasonal_naive")}


def test_evaluate_returns_tidy_results_per_market_and_fold():
    df = _sample()
    cfg = BacktestConfig(horizon=14, n_folds=2)
    results = evaluate(df, _simple_forecasters(), cfg)

    assert list(results.columns) == ["model", "market", "fold", "metric", "value"]
    assert not results.empty
    assert "wrmsse" in set(results["metric"])
    assert set(results["fold"]) == {0, 1}
    # per-market: sample is India-only, so exactly one market appears.
    assert set(results["market"]) == set(df["market"].unique())


def test_evaluate_reports_all_supporting_metrics():
    results = evaluate(_sample(), _simple_forecasters(), BacktestConfig(horizon=14, n_folds=1))
    assert {"mae", "rmse", "mape", "smape", "wape", "wrmsse"} <= set(results["metric"])


def test_leaderboard_pivot_has_overall_column():
    results = evaluate(_sample(), _simple_forecasters(), BacktestConfig(horizon=14, n_folds=2))
    pivot = leaderboard_pivot(build_leaderboard(results), metric="wrmsse")
    assert "overall" in pivot.columns
    assert set(pivot.index) <= {"naive", "seasonal_naive"}


def test_select_top_series_caps_series_per_market():
    df = _sample()
    top = select_top_series(df, n=2, per_market=True)
    counts = top.groupby("market")[["store_id", "sku_id"]].apply(
        lambda g: g.drop_duplicates().shape[0]
    )
    assert (counts <= 2).all()
