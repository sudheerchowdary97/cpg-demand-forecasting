"""Tests for the Task 4 simple baselines + registry."""

from __future__ import annotations

import pandas as pd

from cpg_forecast.baselines import available, get
from cpg_forecast.data import DataConfig, generate
from cpg_forecast.features.splits import time_split


def _sample() -> pd.DataFrame:
    return generate(DataConfig.sample())


def _weekly_series() -> pd.DataFrame:
    """One series whose demand depends only on day-of-week (units = dow * 10)."""
    dates = pd.date_range("2023-01-02", periods=21, freq="D")  # 3 whole weeks
    return pd.DataFrame(
        {
            "store_id": "S1",
            "sku_id": "A",
            "date": dates,
            "units": dates.dayofweek.to_numpy() * 10.0,
        }
    )


# ---- registry -------------------------------------------------------------


def test_registry_exposes_full_roadmap_set():
    names = set(available())
    expected = {
        "naive",
        "seasonal_naive",
        "moving_average",
        "drift",
        "ets",
        "arima",
        "sarimax",
        "var",
        "prophet",
        "lightgbm",
        "xgboost",
    }
    assert expected <= names


# ---- naive / seasonal-naive semantics -------------------------------------


def test_naive_predicts_last_training_value():
    train = _weekly_series()
    test = pd.DataFrame({"store_id": ["S1"], "sku_id": ["A"], "date": [pd.Timestamp("2023-01-23")]})
    pred = get("naive")().fit(train).predict(test)
    assert pred.iloc[0] == train["units"].iloc[-1]


def test_seasonal_naive_uses_same_weekday():
    train = _weekly_series()
    # 2023-01-25 is a Wednesday (dow=2) → seasonal-naive should predict 2*10 = 20.
    test = pd.DataFrame({"store_id": ["S1"], "sku_id": ["A"], "date": [pd.Timestamp("2023-01-25")]})
    pred = get("seasonal_naive")().fit(train).predict(test)
    assert pred.iloc[0] == 20.0


# ---- shared contract across simple baselines ------------------------------


def test_simple_baselines_are_aligned_nonnegative_and_complete():
    split = time_split(_sample(), val_days=14, test_days=14)
    for name in ("naive", "seasonal_naive", "moving_average", "drift"):
        pred = get(name)().fit(split.train).predict(split.test)
        assert pred.index.equals(split.test.index)  # aligned to test rows
        assert pred.notna().all()  # unseen series fall back, never NaN
        assert (pred >= 0).all()  # demand can't be negative
