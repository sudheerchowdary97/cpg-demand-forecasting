"""Lag & rolling-window features (Task 3).

EDA found ACF spikes at lags 7/14/21/28 (strong weekly cycle) — see
docs/eda_findings.md. Every feature here is computed *causally* per series
(market, store_id, sku_id): rolling stats are shifted by one day first, so a
day's features only ever see strictly earlier days. Getting this wrong would
leak the future into training and inflate backtest scores in Task 4+.
"""

from __future__ import annotations

import pandas as pd

SERIES_KEY = ["store_id", "sku_id"]
LAGS = (7, 14, 21, 28)
ROLLING_WINDOWS = (7, 28)


def add_lag_features(
    df: pd.DataFrame,
    target: str = "units",
    lags: tuple[int, ...] = LAGS,
    windows: tuple[int, ...] = ROLLING_WINDOWS,
) -> pd.DataFrame:
    """Add causal lag and rolling mean/std features, one series at a time.

    Assumes one row per (store_id, sku_id, date) and that `df` covers a
    contiguous date range per series (gaps from cold-start listings are fine;
    the frame just starts later for that series).
    """
    out = df.sort_values(SERIES_KEY + ["date"]).reset_index(drop=True)
    grouped = out.groupby(SERIES_KEY, observed=True)[target]

    for lag in lags:
        out[f"{target}_lag{lag}"] = grouped.shift(lag)

    # Shift(1) first so the rolling window never includes the current day.
    out["_shifted"] = grouped.shift(1)
    shifted_grouped = out.groupby(SERIES_KEY, observed=True)["_shifted"]
    for window in windows:
        out[f"{target}_roll_mean{window}"] = shifted_grouped.transform(
            lambda s, w=window: s.rolling(w, min_periods=1).mean()
        )
        out[f"{target}_roll_std{window}"] = shifted_grouped.transform(
            lambda s, w=window: s.rolling(w, min_periods=2).std()
        )
    out = out.drop(columns="_shifted")

    return out
