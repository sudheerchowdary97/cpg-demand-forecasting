"""Feature engineering pipeline (Task 3).

Builds lag/rolling, calendar, price/promo, and categorical-embedding-code
features on top of the Task 1 synthetic dataset, driven by Task 2 EDA
findings (docs/eda_findings.md). Leakage-free: category vocabularies are fit
on the train split only; lag/rolling stats are always causal.
"""

from cpg_forecast.features.calendar import add_calendar_features
from cpg_forecast.features.encoding import EMBEDDING_COLUMNS, CategoryEncoder
from cpg_forecast.features.lags import LAGS, ROLLING_WINDOWS, add_lag_features
from cpg_forecast.features.pipeline import build_features
from cpg_forecast.features.price import add_price_features
from cpg_forecast.features.splits import Split, rolling_origin_splits, time_split

__all__ = [
    "add_calendar_features",
    "add_price_features",
    "add_lag_features",
    "LAGS",
    "ROLLING_WINDOWS",
    "CategoryEncoder",
    "EMBEDDING_COLUMNS",
    "Split",
    "time_split",
    "rolling_origin_splits",
    "build_features",
]
