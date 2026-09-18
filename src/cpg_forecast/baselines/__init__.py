"""Task 4 baselines — the bar every deep model must beat.

Importing this package registers every baseline (simple, statistical, prophet,
ml) in the name→class registry so the CLI and tests can select them by string.
Heavy backends (statsmodels/prophet/lightgbm/xgboost) are imported lazily inside
each model, so importing the package itself never requires the optional deps.
"""

from cpg_forecast.baselines import ml, prophet_model, simple, statistical  # noqa: F401
from cpg_forecast.baselines.base import Baseline, available, get, register

__all__ = ["Baseline", "available", "get", "register"]
