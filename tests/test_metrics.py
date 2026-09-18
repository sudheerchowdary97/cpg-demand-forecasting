"""Tests for the Task 4 metrics module."""

from __future__ import annotations

import numpy as np

from cpg_forecast.eval import metrics as M

# ---- point metrics --------------------------------------------------------


def test_perfect_forecast_is_zero_error():
    y = [1.0, 2.0, 3.0, 4.0]
    assert M.mae(y, y) == 0.0
    assert M.rmse(y, y) == 0.0
    assert M.wape(y, y) == 0.0
    assert M.smape(y, y) == 0.0


def test_mape_ignores_zero_actuals():
    # Only the non-zero actual (10 vs 11) contributes: |10-11|/10 = 10%.
    assert np.isclose(M.mape([0.0, 10.0], [5.0, 11.0]), 10.0)


def test_wape_handles_all_zero_actuals():
    assert np.isnan(M.wape([0.0, 0.0], [1.0, 2.0]))


# ---- scaling / RMSSE ------------------------------------------------------


def test_naive_scale_flat_or_short_series_is_nan():
    assert np.isnan(M.naive_scale([3.0, 3.0, 3.0]))  # zero variation
    assert np.isnan(M.naive_scale([5.0]))  # too short


def test_rmsse_matches_closed_form():
    scale = M.naive_scale([1.0, 2.0, 3.0, 4.0, 5.0])  # unit steps → scale 1.0
    assert np.isclose(scale, 1.0)
    # errors [1, 2] → mse 2.5 → rmsse sqrt(2.5)
    assert np.isclose(M.rmsse([6.0, 7.0], [5.0, 5.0], scale), np.sqrt(2.5))


def test_rmsse_zero_scale_is_nan():
    assert np.isnan(M.rmsse([1.0, 2.0], [1.0, 2.0], 0.0))


# ---- WRMSSE aggregation ---------------------------------------------------


def test_weighted_rmsse_is_weighted_mean():
    # (1*1 + 3*3) / (1 + 3) = 2.5
    assert np.isclose(M.weighted_rmsse([1.0, 3.0], [1.0, 3.0]), 2.5)


def test_weighted_rmsse_skips_nan_series():
    # Second series has NaN RMSSE → only the first (weight 2) counts.
    assert np.isclose(M.weighted_rmsse([1.0, np.nan], [2.0, 5.0]), 1.0)


def test_weighted_rmsse_all_zero_weight_is_nan():
    assert np.isnan(M.weighted_rmsse([1.0, 2.0], [0.0, 0.0]))
