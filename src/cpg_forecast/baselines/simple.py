"""Simple, vectorised baselines (Task 4).

Naive, seasonal-naive (weekly), moving-average and drift. Pure numpy/pandas, so
they run full-scale on the Mac and set the first bar to beat. All are strictly
leakage-free: every forecast uses only training rows up to the fold origin, and
the weekly seasonal-naive repeats the last observed value *per weekday* rather
than peeking at same-week test actuals (the EDA showed a strong weekly cycle).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cpg_forecast.baselines.base import SERIES_KEY, Baseline, register, series_index


@register("naive")
class Naive(Baseline):
    """Forecast = each series' last observed training value."""

    def fit(self, train: pd.DataFrame, target: str = "units") -> Naive:
        self.fallback_ = float(train[target].mean())
        self.last_ = train.sort_values("date").groupby(SERIES_KEY, observed=True)[target].last()
        return self

    def predict(self, test: pd.DataFrame) -> pd.Series:
        values = self.last_.reindex(series_index(test)).to_numpy()
        return self._finish(values, test)


@register("seasonal_naive")
class SeasonalNaive(Baseline):
    """Weekly seasonal naive: last observed value for the same day-of-week."""

    def fit(self, train: pd.DataFrame, target: str = "units") -> SeasonalNaive:
        self.fallback_ = float(train[target].mean())
        t = train.sort_values("date").copy()
        t["_dow"] = pd.to_datetime(t["date"]).dt.dayofweek
        self.by_dow_ = t.groupby(SERIES_KEY + ["_dow"], observed=True)[target].last()
        self.last_ = t.groupby(SERIES_KEY, observed=True)[target].last()
        return self

    def predict(self, test: pd.DataFrame) -> pd.Series:
        dow = pd.to_datetime(test["date"]).dt.dayofweek
        idx = pd.MultiIndex.from_arrays([test["store_id"], test["sku_id"], dow])
        values = self.by_dow_.reindex(idx).to_numpy()
        # Fall back to the series' last value where a weekday was never seen.
        series_last = self.last_.reindex(series_index(test)).to_numpy()
        values = np.where(np.isfinite(values), values, series_last)
        return self._finish(values, test)


@register("moving_average")
class MovingAverage(Baseline):
    """Forecast = mean of each series' last `window` training observations."""

    def __init__(self, horizon: int = 28, window: int = 28) -> None:
        super().__init__(horizon=horizon)
        self.window = window

    def fit(self, train: pd.DataFrame, target: str = "units") -> MovingAverage:
        self.fallback_ = float(train[target].mean())
        grouped = train.sort_values("date").groupby(SERIES_KEY, observed=True)[target]
        self.avg_ = grouped.apply(lambda s: s.tail(self.window).mean())
        return self

    def predict(self, test: pd.DataFrame) -> pd.Series:
        values = self.avg_.reindex(series_index(test)).to_numpy()
        return self._finish(values, test)


@register("drift")
class Drift(Baseline):
    """Linear drift: last value + slope × days-ahead, slope from train endpoints."""

    def fit(self, train: pd.DataFrame, target: str = "units") -> Drift:
        self.fallback_ = float(train[target].mean())
        self.origin_ = pd.to_datetime(train["date"]).max()

        def _endpoints(s: pd.Series) -> pd.Series:
            n = len(s)
            last = float(s.iloc[-1])
            slope = (last - float(s.iloc[0])) / (n - 1) if n > 1 else 0.0
            return pd.Series({"last": last, "slope": slope})

        grouped = train.sort_values("date").groupby(SERIES_KEY, observed=True)[target]
        self.params_ = grouped.apply(_endpoints).unstack()
        return self

    def predict(self, test: pd.DataFrame) -> pd.Series:
        idx = series_index(test)
        last = self.params_["last"].reindex(idx).to_numpy()
        slope = self.params_["slope"].reindex(idx).to_numpy()
        steps = (pd.to_datetime(test["date"]) - self.origin_).dt.days.to_numpy()
        return self._finish(last + slope * steps, test)
