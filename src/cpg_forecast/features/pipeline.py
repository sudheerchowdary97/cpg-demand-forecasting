"""End-to-end feature pipeline (Task 3).

CLI:  python -m cpg_forecast.features --out data/processed/features.parquet
"""

from __future__ import annotations

import pandas as pd

from cpg_forecast.features.calendar import add_calendar_features
from cpg_forecast.features.encoding import CategoryEncoder
from cpg_forecast.features.lags import add_lag_features
from cpg_forecast.features.price import add_price_features
from cpg_forecast.features.splits import time_split


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add calendar, price, and lag/rolling features. Does not encode categoricals.

    Categorical codes are deliberately left out here: `CategoryEncoder` must be
    fit on the train split only (see splits.py) to avoid leaking val/test
    categories into the vocabulary, so encoding happens after `time_split`.
    """
    out = add_calendar_features(df)
    out = add_price_features(out)
    out = add_lag_features(out)
    return out


def build_dataset(
    df: pd.DataFrame, val_days: int = 28, test_days: int = 28
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, CategoryEncoder]:
    """Full pipeline: engineer features, split chronologically, fit encoder on train."""
    featured = build_features(df)
    split = time_split(featured, val_days=val_days, test_days=test_days)

    encoder = CategoryEncoder().fit(split.train)
    train = encoder.transform(split.train)
    val = encoder.transform(split.val)
    test = encoder.transform(split.test)
    return train, val, test, encoder
