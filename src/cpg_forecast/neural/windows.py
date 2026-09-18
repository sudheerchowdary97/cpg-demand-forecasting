"""Flattened-window feature assembly for the Task 5 MLP.

The MLP consumes an *explicit* lookback window — the last `L` days of `units`
flattened into a vector — plus target-day covariates (calendar + price) and the
categorical codes that feed entity embeddings. This is the literal "feed-forward
over flattened window + embeddings" from the roadmap.

The window is built by reusing the Task 3 `add_lag_features` with `lags=1..L`
(and no rolling stats), so the same causal, leakage-free machinery that powers
the baselines also powers the MLP — they can never drift apart. `units` is
modelled in `log1p` space (counts are right-skewed with a zero spike) and the
numeric block is standardised with stats fit on train only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cpg_forecast.features.calendar import add_calendar_features
from cpg_forecast.features.encoding import EMBEDDING_COLUMNS
from cpg_forecast.features.lags import add_lag_features
from cpg_forecast.features.price import add_price_features

DEFAULT_WINDOW = 28
TARGET = "units"

# Target-day covariates (known for future dates — no target leakage).
COVARIATE_COLS = [
    "dow",
    "is_weekend",
    "month",
    "doy_sin",
    "doy_cos",
    "is_holiday",
    "price",
    "base_price",
    "promo_flag",
    "temp_c",
    "discount_pct",
]
# Categorical codes → nn.Embedding inputs (order matches EMBEDDING_COLUMNS).
CODE_COLS = [f"{c}_code" for c in EMBEDDING_COLUMNS]


def window_cols(window: int) -> list[str]:
    """Column names of the flattened window: the last `window` daily lags."""
    return [f"{TARGET}_lag{k}" for k in range(1, window + 1)]


def add_window_features(
    df: pd.DataFrame, window: int = DEFAULT_WINDOW, target: str = TARGET
) -> pd.DataFrame:
    """Add calendar + price covariates and the `window` past-`units` lags."""
    out = add_price_features(add_calendar_features(df))
    return add_lag_features(out, target=target, lags=tuple(range(1, window + 1)), windows=())


def assemble_numeric(frame: pd.DataFrame, window: int) -> np.ndarray:
    """Numeric model input: log1p(window) ++ covariates, NaNs → 0 (cold-start)."""
    win = np.log1p(np.clip(frame[window_cols(window)].to_numpy(dtype="float64"), 0, None))
    cov = frame[COVARIATE_COLS].to_numpy(dtype="float64")
    numeric = np.concatenate([win, cov], axis=1)
    return np.nan_to_num(numeric, nan=0.0)


def codes_matrix(frame: pd.DataFrame) -> np.ndarray:
    """Integer code matrix (rows × len(EMBEDDING_COLUMNS)) for the embeddings."""
    return frame[CODE_COLS].to_numpy(dtype="int64")


class Standardizer:
    """Column-wise standardiser; std<eps → 1 so constant columns pass through."""

    def fit(self, x: np.ndarray) -> Standardizer:
        self.mean_ = x.mean(axis=0)
        self.std_ = x.std(axis=0)
        self.std_ = np.where(self.std_ < 1e-8, 1.0, self.std_)
        return self

    def transform(self, x: np.ndarray) -> np.ndarray:
        return (x - self.mean_) / self.std_
