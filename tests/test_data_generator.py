"""Tests for the Task 1 synthetic data generator."""

from __future__ import annotations

import pandas as pd
from cpg_forecast.data import DataConfig, generate
from cpg_forecast.data.reference import MARKET_CHANNELS
from cpg_forecast.data.schema import COLUMNS


def _sample() -> pd.DataFrame:
    return generate(DataConfig.sample())


def test_schema_and_nonempty():
    df = _sample()
    assert list(df.columns) == COLUMNS
    assert len(df) > 0


def test_no_missing_or_negative_target():
    df = _sample()
    assert not df["units"].isna().any()
    assert (df["units"] >= 0).all()
    assert (df["price"] > 0).all()


def test_deterministic():
    a = _sample()
    b = _sample()
    assert a.equals(b), "same config must reproduce the same data"


def test_channels_belong_to_market():
    df = _sample()
    for market, sub in df.groupby("market"):
        valid = {c for c, _r, _w in MARKET_CHANNELS[market]}
        assert set(sub["channel"]).issubset(valid)


def test_hierarchy_and_promo():
    df = _sample()
    # every store maps to exactly one channel + retailer + market (static attributes)
    per_store = df.groupby("store_id")[["market", "channel", "retailer"]].nunique()
    assert (per_store == 1).all().all()
    # promotions exist and carry a price discount vs base
    promo = df[df["promo_flag"] == 1]
    assert len(promo) > 0
    assert (promo["price"] <= promo["base_price"]).all()
