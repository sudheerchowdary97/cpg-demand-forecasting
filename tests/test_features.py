"""Tests for the Task 3 feature pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cpg_forecast.data import DataConfig, generate
from cpg_forecast.features import (
    CategoryEncoder,
    add_calendar_features,
    add_lag_features,
    add_price_features,
    rolling_origin_splits,
    time_split,
)
from cpg_forecast.features.pipeline import build_dataset, build_features


def _sample() -> pd.DataFrame:
    return generate(DataConfig.sample())


# ---- calendar ---------------------------------------------------------


def test_calendar_features_weekend_and_holiday_flags():
    df = _sample()
    out = add_calendar_features(df)
    date = pd.to_datetime(out["date"])
    assert (out["is_weekend"] == (date.dt.dayofweek >= 4).astype(int)).all()
    assert (out["is_holiday"] == (out["holiday"] != "").astype(int)).all()
    assert out["dow"].between(0, 6).all()
    assert out["month"].between(1, 12).all()


def test_calendar_cyclical_encoding_is_bounded():
    df = _sample()
    out = add_calendar_features(df)
    assert out["doy_sin"].between(-1.0, 1.0).all()
    assert out["doy_cos"].between(-1.0, 1.0).all()


# ---- price --------------------------------------------------------------


def test_price_discount_matches_promo_flag():
    df = _sample()
    out = add_price_features(df)
    promo = out[out["promo_flag"] == 1]
    non_promo = out[out["promo_flag"] == 0]
    assert (promo["discount_pct"] > 0).all()
    assert np.isclose(non_promo["discount_pct"], 0).all()


# ---- lags / rolling -------------------------------------------------------


def test_lag_features_causal_no_future_leakage():
    df = _sample()
    out = add_lag_features(df)
    one = out[(out["store_id"] == out["store_id"].iloc[0])].sort_values("date")
    one = one[one["sku_id"] == one["sku_id"].iloc[0]].reset_index(drop=True)
    # lag7 on day i must equal units on day i-7 for that series.
    aligned = one["units"].shift(7)
    valid = aligned.notna()
    assert np.allclose(one.loc[valid, "units_lag7"], aligned[valid])


def test_rolling_mean_excludes_current_day():
    """A single extreme spike must not appear in its own day's rolling mean."""
    df = pd.DataFrame(
        {
            "store_id": ["S1"] * 10,
            "sku_id": ["A"] * 10,
            "date": pd.date_range("2023-01-01", periods=10),
            "units": [1.0] * 5 + [1000.0] + [1.0] * 4,
        }
    )
    out = add_lag_features(df, lags=(1,), windows=(3,))
    spike_row = out.iloc[5]
    assert spike_row["units"] == 1000.0
    assert spike_row["units_roll_mean3"] < 10  # window is the 3 days *before* the spike


def test_lag_features_respect_series_boundaries():
    """Series A's lag features must never pull values from series B."""
    df = pd.DataFrame(
        {
            "store_id": ["S1"] * 5 + ["S2"] * 5,
            "sku_id": ["A"] * 10,
            "date": list(pd.date_range("2023-01-01", periods=5)) * 2,
            "units": [10.0] * 5 + [999.0] * 5,
        }
    )
    out = add_lag_features(df, lags=(1,), windows=(3,))
    s1 = out[out["store_id"] == "S1"].sort_values("date")
    assert not (s1["units_lag1"] == 999.0).any()
    assert not (s1["units_roll_mean3"] == 999.0).any()


def test_new_series_start_has_nan_lags():
    df = _sample()
    out = add_lag_features(df)
    first_rows = out.sort_values("date").groupby(["store_id", "sku_id"], observed=True).head(1)
    assert first_rows["units_lag7"].isna().all()


# ---- encoding -------------------------------------------------------------


def test_category_encoder_fit_transform_roundtrip():
    df = _sample()
    enc = CategoryEncoder(columns=["market", "channel"])
    out = enc.fit_transform(df)
    assert (out["market_code"] > 0).all()  # 0 is reserved for unknown
    assert out["market_code"].nunique() == df["market"].nunique()


def test_category_encoder_unseen_category_maps_to_unknown():
    df = _sample()
    enc = CategoryEncoder(columns=["market"]).fit(df[df["market"] != "India"])
    out = enc.transform(df[df["market"] == "India"])
    assert (out["market_code"] == 0).all()


def test_category_encoder_vocab_size():
    df = _sample()
    enc = CategoryEncoder(columns=["market"]).fit(df)
    assert enc.vocab_size("market") == df["market"].nunique() + 1


# ---- splits -----------------------------------------------------------


def test_time_split_is_chronological_and_non_overlapping():
    df = _sample()
    split = time_split(df, val_days=14, test_days=14)
    assert pd.to_datetime(split.train["date"]).max() < pd.to_datetime(split.val["date"]).min()
    assert pd.to_datetime(split.val["date"]).max() < pd.to_datetime(split.test["date"]).min()
    assert len(split.train) + len(split.val) + len(split.test) == len(df)


def test_rolling_origin_splits_expand_and_stay_chronological():
    df = _sample()
    folds = rolling_origin_splits(df, horizon_days=14, n_folds=3)
    assert len(folds) == 3
    train_sizes = [len(f.train) for f in folds]
    assert train_sizes == sorted(train_sizes)  # each fold's train set only grows
    for fold in folds:
        if len(fold.train) and len(fold.test):
            assert (
                pd.to_datetime(fold.train["date"]).max() < pd.to_datetime(fold.test["date"]).min()
            )


# ---- full pipeline ----------------------------------------------------


def test_build_features_adds_expected_columns():
    df = _sample()
    out = build_features(df)
    for col in ("is_weekend", "discount_pct", "units_lag7", "units_roll_mean7"):
        assert col in out.columns


def test_build_dataset_encoder_fit_on_train_only():
    df = _sample()
    train, val, test, encoder = build_dataset(df, val_days=14, test_days=14)
    assert len(train) and len(val) and len(test)
    assert set(encoder.vocabs["market"]) == set(train["market"].unique())
    assert "market_code" in val.columns and "market_code" in test.columns
