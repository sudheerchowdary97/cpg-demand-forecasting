"""Prophet baseline (Task 4).

Facebook/Meta Prophet, fit per series with weekly + yearly seasonality (both
present in the EDA). Prophet is an optional, relatively heavy dependency, so it
runs on a `--sample`/`--top-series` subset on the Mac and is skipped cleanly if
not installed. Reuses `PerSeriesForecaster`'s per-series loop and fallbacks.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from cpg_forecast.baselines.base import PerSeriesForecaster, register

SEASONAL_PERIOD = 7


@register("prophet")
class Prophet(PerSeriesForecaster):
    """Additive model with weekly + yearly seasonality."""

    min_train = 2 * SEASONAL_PERIOD

    def _import(self) -> None:
        import prophet  # noqa: F401

        # Prophet/cmdstanpy are chatty; quiet them so backtest logs stay readable.
        logging.getLogger("prophet").setLevel(logging.ERROR)
        logging.getLogger("cmdstanpy").setLevel(logging.ERROR)

    def _fit_predict_one(self, series: pd.Series) -> np.ndarray:
        from prophet import Prophet as FBProphet

        frame = pd.DataFrame({"ds": series.index, "y": series.to_numpy()})
        model = FBProphet(weekly_seasonality=True, yearly_seasonality=True, daily_seasonality=False)
        model.fit(frame)
        future = model.make_future_dataframe(periods=self.horizon, freq="D")
        forecast = model.predict(future)
        return forecast["yhat"].tail(self.horizon).to_numpy()
