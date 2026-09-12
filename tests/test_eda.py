"""Tests for Task 2 EDA compute helpers (pure functions, small sample)."""

from __future__ import annotations

import numpy as np

from cpg_forecast.data import DataConfig, generate
from cpg_forecast.eda import acf, compute_findings


def _df():
    df = generate(DataConfig.sample())
    import pandas as pd

    df["date"] = pd.to_datetime(df["date"])
    df["dow"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["hemisphere"] = np.where(df["market"] == "Australia", "Southern", "Northern")
    return df


def test_acf_lag0_is_one():
    assert abs(acf(np.arange(50.0), 5)[0] - 1.0) < 1e-9


def test_findings_keys_and_ranges():
    f = compute_findings(_df())
    for k in ["rows", "total_units", "zero_pct", "promo_uplift", "weekend_lift"]:
        assert k in f
    assert f["rows"] > 0
    assert 0 <= f["zero_pct"] <= 100
    assert f["promo_uplift"] > 1.0  # promotions must lift demand
