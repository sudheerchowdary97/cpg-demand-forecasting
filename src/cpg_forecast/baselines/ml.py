"""Gradient-boosted baselines (Task 4) — LightGBM & XGBoost.

Tree models trained on the Task 3 engineered features (calendar, price, lags,
rolling stats, categorical codes). They are fit per market (the harness slices
per market) on the training rows, then forecast the horizon **recursively**:
day d's lag/rolling features are recomputed from actual history plus the model's
own predictions for days < d. That recursion is what keeps them leakage-free —
using the pre-computed lag columns directly would let day d "see" test actuals
from day d−7. Feature engineering is reused verbatim from `cpg_forecast.features`
so baselines and the Task 3 pipeline can never drift apart.

LightGBM/XGBoost are optional deps; `_import` raising is caught by the harness.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cpg_forecast.baselines.base import Baseline, register
from cpg_forecast.features.calendar import add_calendar_features
from cpg_forecast.features.encoding import EMBEDDING_COLUMNS, CategoryEncoder
from cpg_forecast.features.lags import LAGS, ROLLING_WINDOWS, SERIES_KEY, add_lag_features
from cpg_forecast.features.price import add_price_features

_CALENDAR_COLS = ["dow", "is_weekend", "month", "doy_sin", "doy_cos", "is_holiday"]
_PRICE_COLS = ["price", "base_price", "promo_flag", "temp_c", "discount_pct"]
_CODE_COLS = [f"{c}_code" for c in EMBEDDING_COLUMNS]
_LAG_COLS = (
    [f"units_lag{lag}" for lag in LAGS]
    + [f"units_roll_mean{w}" for w in ROLLING_WINDOWS]
    + [f"units_roll_std{w}" for w in ROLLING_WINDOWS]
)
_STATIC_COLS = _CALENDAR_COLS + _PRICE_COLS + _CODE_COLS
_FEATURE_COLS = _STATIC_COLS + _LAG_COLS
# History (days) to keep before the origin so lag/rolling windows are covered.
_LOOKBACK = max(max(LAGS), max(ROLLING_WINDOWS)) + 5


class _GBMForecaster(Baseline):
    """Shared fit + recursive-forecast logic; subclasses supply the regressor."""

    def _import(self) -> None: ...

    def _make_model(self):
        raise NotImplementedError

    def fit(self, train: pd.DataFrame, target: str = "units") -> _GBMForecaster:
        self._import()
        self.fallback_ = float(train[target].mean())

        feats = add_lag_features(add_price_features(add_calendar_features(train)))
        self.encoder_ = CategoryEncoder().fit(feats)
        feats = self.encoder_.transform(feats)

        self.model_ = self._make_model()
        self.model_.fit(feats[_FEATURE_COLS], feats[target])

        # Keep just enough recent raw history per series for recursive lags.
        origin = pd.to_datetime(train["date"]).max()
        cutoff = origin - pd.Timedelta(days=_LOOKBACK)
        cols = SERIES_KEY + ["date", target]
        hist = train[pd.to_datetime(train["date"]) > cutoff][cols].copy()
        hist["date"] = pd.to_datetime(hist["date"]).dt.normalize()
        self.history_ = hist
        self.target_ = target
        return self

    def predict(self, test: pd.DataFrame) -> pd.Series:
        te = test.copy()
        te["date"] = pd.to_datetime(te["date"]).dt.normalize()

        # Covariates known for future dates (no dependence on the target).
        static = self.encoder_.transform(add_price_features(add_calendar_features(te)))
        static = static.set_index(SERIES_KEY + ["date"])[_STATIC_COLS]

        history = self.history_.copy()
        preds: list[pd.DataFrame] = []
        for day in sorted(te["date"].unique()):
            drows = te[te["date"] == day][SERIES_KEY + ["date"]].copy()
            drows[self.target_] = np.nan

            work = pd.concat([history, drows], ignore_index=True)
            work = add_lag_features(work, target=self.target_)
            lag_part = work[work["date"] == day].set_index(SERIES_KEY + ["date"])[_LAG_COLS]

            x = lag_part.join(static, how="left")[_FEATURE_COLS]
            yhat = np.clip(self.model_.predict(x), 0.0, None)

            filled = x.reset_index()[SERIES_KEY + ["date"]].copy()
            filled[self.target_] = yhat
            preds.append(filled)
            history = pd.concat([history, filled], ignore_index=True)

        pred = pd.concat(preds, ignore_index=True).set_index(SERIES_KEY + ["date"])[self.target_]
        idx = pd.MultiIndex.from_arrays([te["store_id"], te["sku_id"], te["date"]])
        return self._finish(pred.reindex(idx).to_numpy(), test)


@register("lightgbm")
class LightGBM(_GBMForecaster):
    """LightGBM gradient-boosted trees."""

    def _import(self) -> None:
        import lightgbm  # noqa: F401

    def _make_model(self):
        import lightgbm as lgb

        return lgb.LGBMRegressor(
            n_estimators=300,
            learning_rate=0.05,
            num_leaves=31,
            min_child_samples=20,
            subsample=0.8,
            colsample_bytree=0.8,
            n_jobs=-1,
            verbose=-1,
        )


@register("xgboost")
class XGBoost(_GBMForecaster):
    """XGBoost gradient-boosted trees."""

    def _import(self) -> None:
        import xgboost  # noqa: F401

    def _make_model(self):
        import xgboost as xgb

        return xgb.XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            tree_method="hist",
            n_jobs=-1,
            verbosity=0,
        )
