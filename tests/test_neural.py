"""Tests for the Task 5 global MLP forecaster (skipped if torch is absent)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("torch")

from cpg_forecast.data import DataConfig, generate  # noqa: E402
from cpg_forecast.eval import BacktestConfig, evaluate  # noqa: E402
from cpg_forecast.features.splits import time_split  # noqa: E402
from cpg_forecast.neural.forecaster import MLPForecaster  # noqa: E402
from cpg_forecast.neural.windows import add_window_features, window_cols  # noqa: E402


def _sample() -> pd.DataFrame:
    return generate(DataConfig.sample())


def _tiny_mlp(horizon: int = 14, window: int = 14) -> MLPForecaster:
    # Minimal config so tests train in a couple of seconds.
    return MLPForecaster(horizon=horizon, window=window, max_epochs=1, batch_size=256, val_days=14)


def test_window_builder_lag1_is_previous_day():
    out = add_window_features(_sample(), window=14)
    one = out[out["store_id"] == out["store_id"].iloc[0]].sort_values("date")
    one = one[one["sku_id"] == one["sku_id"].iloc[0]].reset_index(drop=True)
    aligned = one["units"].shift(1)
    valid = aligned.notna()
    assert np.allclose(one.loc[valid, "units_lag1"], aligned[valid])
    assert len(window_cols(14)) == 14


def test_mlp_forecaster_predicts_aligned_nonnegative_complete():
    split = time_split(_sample(), val_days=14, test_days=14)
    model = _tiny_mlp().fit(split.train)
    pred = model.predict(split.test)
    assert pred.index.equals(split.test.index)  # aligned to test rows
    assert pred.notna().all()  # unseen series fall back, never NaN
    assert (pred >= 0).all()  # demand can't be negative


def test_mlp_runs_in_global_backtest():
    df = _sample()
    cfg = BacktestConfig(horizon=7, n_folds=1, fit_scope="global")
    results = evaluate(df, {"mlp": lambda: _tiny_mlp(horizon=7)}, cfg)
    assert "mlp" in set(results["model"])
    assert "wrmsse" in set(results["metric"])
    assert results[results["metric"] == "wrmsse"]["value"].notna().any()
