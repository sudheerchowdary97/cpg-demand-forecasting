"""Baseline forecasters — shared base + registry (Task 4).

Baselines are "the bar every deep model must beat". Each one implements the
`Forecaster` contract from `eval.backtest` (fit on a fold's train rows, predict
one value per test row). A tiny name→class registry lets the CLI select models
by string (`--models naive,seasonal_naive,...`).

`PerSeriesForecaster` factors out the common univariate loop used by the
classical models (ETS/ARIMA/SARIMAX/Prophet): fit one model per (store, sku)
series, forecast `horizon` steps past the training origin, and look those
forecasts up per test row. It is deliberately defensive — a series that is too
short or fails to fit falls back to its last value rather than aborting.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

SERIES_KEY = ["store_id", "sku_id"]

_REGISTRY: dict[str, type[Baseline]] = {}


def register(name: str):
    """Class decorator: register a baseline under `name` and set `cls.name`."""

    def _decorate(cls: type[Baseline]) -> type[Baseline]:
        cls.name = name
        _REGISTRY[name] = cls
        return cls

    return _decorate


def available() -> list[str]:
    """Sorted names of all registered baselines."""
    return sorted(_REGISTRY)


def get(name: str) -> type[Baseline]:
    """Look up a baseline class by registered name."""
    if name not in _REGISTRY:
        raise KeyError(f"unknown baseline {name!r}; available: {available()}")
    return _REGISTRY[name]


def series_index(df: pd.DataFrame) -> pd.MultiIndex:
    """(store_id, sku_id) MultiIndex used to align per-series stats to rows."""
    return pd.MultiIndex.from_arrays([df["store_id"], df["sku_id"]])


class Baseline(ABC):
    """Common base: holds the forecast horizon and a global fallback level."""

    name: str = "baseline"

    def __init__(self, horizon: int = 28) -> None:
        self.horizon = horizon
        self.fallback_: float = 0.0

    @abstractmethod
    def fit(self, train: pd.DataFrame) -> Baseline: ...

    @abstractmethod
    def predict(self, test: pd.DataFrame) -> pd.Series: ...

    def _finish(self, values: np.ndarray, test: pd.DataFrame) -> pd.Series:
        """Fill unseen-series NaNs with the global mean and clip to non-negative."""
        values = np.where(np.isfinite(values), values, self.fallback_)
        return pd.Series(np.clip(values, 0.0, None), index=test.index)


class PerSeriesForecaster(Baseline):
    """Fit one univariate model per series, forecasting `horizon` steps ahead."""

    #: statsmodels/prophet-style backends need a minimum history to be stable.
    min_train: int = 14

    def _import(self) -> None:
        """Import the heavy backend; raising here lets the harness skip cleanly."""

    def _fit_predict_one(self, series: pd.Series) -> np.ndarray:
        """Fit on a daily `series` (indexed by date) and return `horizon` values."""
        raise NotImplementedError

    @staticmethod
    def _daily(group: pd.DataFrame, target: str = "units") -> pd.Series:
        """Regular daily series over [min, max] date; gaps filled with 0 demand."""
        s = group.set_index(pd.to_datetime(group["date"]))[target].sort_index()
        s = s[~s.index.duplicated(keep="last")]
        full = pd.date_range(s.index.min(), s.index.max(), freq="D")
        return s.reindex(full).fillna(0.0)

    def fit(self, train: pd.DataFrame, target: str = "units") -> PerSeriesForecaster:
        self._import()
        self.fallback_ = float(train[target].mean())
        origin = pd.to_datetime(train["date"]).max()
        self.future_ = pd.date_range(origin + pd.Timedelta(days=1), periods=self.horizon, freq="D")

        rows: list[tuple] = []
        for (store, sku), g in train.groupby(SERIES_KEY, observed=True):
            s = self._daily(g, target)
            if len(s) < self.min_train:
                fc = np.full(self.horizon, s.iloc[-1] if len(s) else self.fallback_)
            else:
                try:
                    fc = np.asarray(self._fit_predict_one(s), dtype=float)
                except Exception:  # noqa: BLE001 — degrade to naive for this series
                    fc = np.full(self.horizon, s.iloc[-1])
            fc = np.clip(
                np.nan_to_num(fc, nan=float(s.iloc[-1] if len(s) else self.fallback_)), 0, None
            )
            for d, v in zip(self.future_, fc, strict=False):
                rows.append((store, sku, d, float(v)))

        pred = pd.DataFrame(rows, columns=["store_id", "sku_id", "date", "_yhat"])
        self._pred_ = pred.set_index(["store_id", "sku_id", "date"])["_yhat"]
        return self

    def predict(self, test: pd.DataFrame) -> pd.Series:
        idx = pd.MultiIndex.from_arrays(
            [test["store_id"], test["sku_id"], pd.to_datetime(test["date"]).dt.normalize()]
        )
        values = self._pred_.reindex(idx).to_numpy()
        return self._finish(values, test)
