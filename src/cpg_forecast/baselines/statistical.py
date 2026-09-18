"""Classical statistical baselines (Task 4) — statsmodels backends.

ETS, ARIMA and SARIMAX are fit per series via `PerSeriesForecaster`; VAR is
different (multivariate) and is fit per market on category-aggregated daily
totals, then disaggregated back to series by each series' training share of its
category. These per-series fits are the heavy part of Task 4, so on the Mac they
run on a `--sample`/`--top-series` subset — full-scale fits belong on cloud.

statsmodels is an optional dependency: `_import` raises if it's missing, which
the backtest harness catches and skips (the run still produces the simple
baselines). Weekly seasonality (period 7) is used throughout, per the EDA.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from cpg_forecast.baselines.base import SERIES_KEY, Baseline, PerSeriesForecaster, register

SEASONAL_PERIOD = 7


@register("ets")
class ETS(PerSeriesForecaster):
    """Holt-Winters exponential smoothing (additive trend + weekly seasonality)."""

    min_train = 2 * SEASONAL_PERIOD  # need two seasons to estimate seasonality

    def _import(self) -> None:
        import statsmodels  # noqa: F401

    def _fit_predict_one(self, series: pd.Series) -> np.ndarray:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = ExponentialSmoothing(
                series,
                trend="add",
                seasonal="add",
                seasonal_periods=SEASONAL_PERIOD,
                initialization_method="estimated",
            ).fit()
        return model.forecast(self.horizon).to_numpy()


@register("arima")
class ARIMA(PerSeriesForecaster):
    """Non-seasonal ARIMA(2,1,2) — a plain autoregressive integrated baseline."""

    def _import(self) -> None:
        import statsmodels  # noqa: F401

    def _fit_predict_one(self, series: pd.Series) -> np.ndarray:
        from statsmodels.tsa.arima.model import ARIMA as SM_ARIMA

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = SM_ARIMA(series, order=(2, 1, 2)).fit()
        return np.asarray(res.forecast(self.horizon))


@register("sarimax")
class SARIMAX(PerSeriesForecaster):
    """Seasonal ARIMA (1,1,1)(1,0,1,7) — adds the weekly seasonal component."""

    min_train = 2 * SEASONAL_PERIOD

    def _import(self) -> None:
        import statsmodels  # noqa: F401

    def _fit_predict_one(self, series: pd.Series) -> np.ndarray:
        from statsmodels.tsa.statespace.sarimax import SARIMAX as SM_SARIMAX

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = SM_SARIMAX(
                series,
                order=(1, 1, 1),
                seasonal_order=(1, 0, 1, SEASONAL_PERIOD),
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False)
        return np.asarray(res.forecast(self.horizon))


@register("var")
class VAR(Baseline):
    """Vector autoregression on per-market, category-aggregated daily totals.

    A single univariate series can't express cross-category dynamics, so VAR is
    fit on the (Food, Beverage) daily totals for the market, then each series'
    forecast is its category's forecast × the series' training share of that
    category. Runs once per market (the harness already slices per market).
    """

    def __init__(self, horizon: int = 28, maxlags: int = 7) -> None:
        super().__init__(horizon=horizon)
        self.maxlags = maxlags

    def fit(self, train: pd.DataFrame, target: str = "units") -> VAR:
        from statsmodels.tsa.api import VAR as SM_VAR

        self.fallback_ = float(train[target].mean())
        t = train.copy()
        t["date"] = pd.to_datetime(t["date"]).dt.normalize()

        # Daily totals per category (Food/Beverage) → wide multivariate frame.
        wide = t.groupby(["date", "category"], observed=True)[target].sum().unstack("category")
        full = pd.date_range(wide.index.min(), wide.index.max(), freq="D")
        wide = wide.reindex(full).fillna(0.0)
        self.categories_ = list(wide.columns)

        origin = wide.index.max()
        self.future_ = pd.date_range(origin + pd.Timedelta(days=1), periods=self.horizon, freq="D")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = SM_VAR(wide.to_numpy()).fit(maxlags=self.maxlags)
            fc = res.forecast(wide.to_numpy()[-res.k_ar :], self.horizon)
        self.cat_fc_ = pd.DataFrame(fc, index=self.future_, columns=self.categories_).clip(lower=0)

        # Each series' share of its category's total demand over the training window.
        series_tot = t.groupby(SERIES_KEY + ["category"], observed=True)[target].sum()
        cat_tot = t.groupby("category", observed=True)[target].sum()
        self.share_ = (
            series_tot / cat_tot.reindex(series_tot.index.get_level_values("category")).to_numpy()
        )
        return self

    def predict(self, test: pd.DataFrame) -> pd.Series:
        te = test.copy()
        te["date"] = pd.to_datetime(te["date"]).dt.normalize()

        # Category forecast for each row's (date, category).
        long_fc = self.cat_fc_.reset_index(names="date").melt(
            id_vars="date", var_name="category", value_name="_catfc"
        )
        cat_lookup = long_fc.set_index(["date", "category"])["_catfc"]
        cat_vals = cat_lookup.reindex(
            pd.MultiIndex.from_arrays([te["date"], te["category"]])
        ).to_numpy()

        # Series share of its category (index has an extra 'category' level to drop).
        share = self.share_.droplevel("category")
        share_vals = share.reindex(
            pd.MultiIndex.from_arrays([te["store_id"], te["sku_id"]])
        ).to_numpy()

        return self._finish(cat_vals * share_vals, test)
