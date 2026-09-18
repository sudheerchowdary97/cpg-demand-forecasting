"""Leakage-free time-based splits (Task 3).

Standard requirement for time series: splits must respect chronology so
lag/rolling features never peek into the future and CategoryEncoder vocabs
are fit only on the training window. Supports both a single train/val/test
cut and rolling-origin folds for backtesting (Task 4+).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Split:
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame


def time_split(
    df: pd.DataFrame,
    val_days: int,
    test_days: int,
    date_col: str = "date",
) -> Split:
    """Single chronological split: [..train..][..val..][..test..] by calendar date.

    `val_days`/`test_days` are counted over the full date range, not per
    series, so every series is cut at the same calendar boundary.
    """
    dates = pd.to_datetime(df[date_col])
    max_date = dates.max()
    test_start = max_date - pd.Timedelta(days=test_days - 1)
    val_start = test_start - pd.Timedelta(days=val_days)

    train = df[dates < val_start]
    val = df[(dates >= val_start) & (dates < test_start)]
    test = df[dates >= test_start]
    return Split(train=train, val=val, test=test)


def rolling_origin_splits(
    df: pd.DataFrame,
    horizon_days: int,
    n_folds: int,
    step_days: int | None = None,
    date_col: str = "date",
) -> list[Split]:
    """Expanding-window rolling-origin folds for backtesting (Task 4+).

    Fold k trains on everything before its origin and evaluates on the next
    `horizon_days`; origins step backward by `step_days` (default =
    horizon_days, i.e. non-overlapping evaluation windows) so folds don't
    reuse the same lag/rolling feature history as "new" data.
    """
    if step_days is None:
        step_days = horizon_days
    dates = pd.to_datetime(df[date_col])
    max_date = dates.max()

    folds: list[Split] = []
    test_start = max_date - pd.Timedelta(days=horizon_days - 1)
    for _ in range(n_folds):
        test_end = test_start + pd.Timedelta(days=horizon_days - 1)
        train = df[dates < test_start]
        test = df[(dates >= test_start) & (dates <= test_end)]
        # No separate val window in the rolling-origin case; empty by convention.
        folds.append(Split(train=train, val=df.iloc[0:0], test=test))
        test_start = test_start - pd.Timedelta(days=step_days)

    return list(reversed(folds))
