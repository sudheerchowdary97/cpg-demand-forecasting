"""Forecast accuracy metrics (Task 4).

The primary project metric is WRMSSE (the M5 competition metric): each series'
squared forecast error is scaled by that series' in-sample one-step naive error,
then weighted by the series' recent dollar sales. Scaling makes errors
comparable across series of wildly different volume (India >> Australia per the
EDA), which is exactly why plain RMSE would let a few high-volume SKUs dominate.

All functions operate on plain numpy arrays so they can be reused unchanged by
the deep-learning models in Tasks 5+. Zero-division is guarded everywhere: this
dataset is ~1.6% zero-demand days, so naive MAPE/scale formulas would otherwise
blow up.
"""

from __future__ import annotations

import numpy as np

# Below this the denominator is treated as zero (flat/degenerate series).
_EPS = 1e-8


def _arr(x) -> np.ndarray:
    return np.asarray(x, dtype=float)


def mae(y_true, y_pred) -> float:
    """Mean absolute error."""
    return float(np.mean(np.abs(_arr(y_true) - _arr(y_pred))))


def rmse(y_true, y_pred) -> float:
    """Root mean squared error."""
    return float(np.sqrt(np.mean((_arr(y_true) - _arr(y_pred)) ** 2)))


def mape(y_true, y_pred) -> float:
    """Mean absolute percentage error over non-zero actuals only (in %).

    Zeros are dropped rather than clipped: a division-by-zero MAPE is undefined,
    and this data has genuine zero-demand days.
    """
    yt, yp = _arr(y_true), _arr(y_pred)
    mask = np.abs(yt) > _EPS
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((yt[mask] - yp[mask]) / yt[mask])) * 100.0)


def smape(y_true, y_pred) -> float:
    """Symmetric MAPE (in %); zero when both actual and forecast are zero."""
    yt, yp = _arr(y_true), _arr(y_pred)
    denom = np.abs(yt) + np.abs(yp)
    num = 2.0 * np.abs(yt - yp)
    out = np.divide(num, denom, out=np.zeros_like(num), where=denom > _EPS)
    return float(np.mean(out) * 100.0)


def wape(y_true, y_pred) -> float:
    """Weighted absolute percentage error = sum|err| / sum|actual| (in %).

    Robust to zeros (aggregates before dividing), which is why it's the
    preferred volume-style error for intermittent CPG demand.
    """
    yt, yp = _arr(y_true), _arr(y_pred)
    denom = np.sum(np.abs(yt))
    if denom <= _EPS:
        return float("nan")
    return float(np.sum(np.abs(yt - yp)) / denom * 100.0)


def pinball_loss(y_true, y_pred, quantile: float) -> float:
    """Quantile (pinball) loss — used for probabilistic forecasts in Task 10."""
    yt, yp = _arr(y_true), _arr(y_pred)
    diff = yt - yp
    return float(np.mean(np.maximum(quantile * diff, (quantile - 1.0) * diff)))


def interval_coverage(y_true, lower, upper) -> float:
    """Empirical coverage: fraction of actuals inside [lower, upper]."""
    yt, lo, hi = _arr(y_true), _arr(lower), _arr(upper)
    return float(np.mean((yt >= lo) & (yt <= hi)))


def naive_scale(train_values) -> float:
    """M5 RMSSE denominator: mean squared one-step naive error over training.

    Returns NaN for series too short or perfectly flat (scale 0) so the caller
    can exclude them from WRMSSE instead of dividing by zero.
    """
    v = _arr(train_values)
    if v.size < 2:
        return float("nan")
    scale = float(np.mean(np.diff(v) ** 2))
    return scale if scale > _EPS else float("nan")


def rmsse(y_true, y_pred, scale: float) -> float:
    """Root Mean Squared Scaled Error for one series given its `naive_scale`."""
    if not np.isfinite(scale) or scale <= _EPS:
        return float("nan")
    mse = float(np.mean((_arr(y_true) - _arr(y_pred)) ** 2))
    return float(np.sqrt(mse / scale))


def weighted_rmsse(rmsse_values, weights) -> float:
    """WRMSSE = sum_i (w_i / sum w) * RMSSE_i, ignoring NaN series/weights."""
    r = _arr(rmsse_values)
    w = _arr(weights)
    mask = np.isfinite(r) & np.isfinite(w) & (w > 0)
    if not mask.any():
        return float("nan")
    w = w[mask]
    return float(np.sum(w / w.sum() * r[mask]))


def point_metrics(y_true, y_pred) -> dict[str, float]:
    """Bundle the scale-free supporting metrics reported alongside WRMSSE."""
    return {
        "mae": mae(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "mape": mape(y_true, y_pred),
        "smape": smape(y_true, y_pred),
        "wape": wape(y_true, y_pred),
    }
