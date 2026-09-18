"""Rolling-origin backtest harness (Task 4).

This is the reusable scoring machinery every later model (Tasks 5–12) plugs
into: give it a long demand frame and a set of forecaster factories, and it
runs per-market, rolling-origin backtests and returns a tidy results frame
`(model, market, fold, metric, value)`.

"Local" is the default: models are fit and scored per market, because the EDA
showed markets differ in scale, seasonality (hemisphere flip) and channel mix,
so a single pooled score would hide who actually wins where. Splitting reuses
`rolling_origin_splits` from the Task 3 feature package — we do NOT reinvent
chronological splitting here.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import pandas as pd

from cpg_forecast.eval import metrics as M
from cpg_forecast.features.splits import rolling_origin_splits

logger = logging.getLogger(__name__)

SERIES_KEY = ["store_id", "sku_id"]


@runtime_checkable
class Forecaster(Protocol):
    """Structural contract every baseline / model must satisfy.

    `fit` sees only a fold's training rows; `predict` returns one forecast per
    row of `test`, aligned to `test.index`. Keeping the interface this small is
    what lets classical baselines and Task 5+ neural nets share one harness.
    """

    name: str

    def fit(self, train: pd.DataFrame) -> Forecaster: ...

    def predict(self, test: pd.DataFrame) -> pd.Series: ...


ForecasterFactory = Callable[[], Forecaster]


@dataclass(frozen=True)
class BacktestConfig:
    """Knobs for a backtest run."""

    horizon: int = 28
    n_folds: int = 3
    step_days: int | None = None  # default = horizon (non-overlapping windows)
    per_market: bool = True
    target: str = "units"
    price_col: str = "price"
    weight_window: int = 28  # last-N training days used for WRMSSE dollar weights


def _group_wrmsse(
    train: pd.DataFrame,
    test: pd.DataFrame,
    preds: pd.Series,
    cfg: BacktestConfig,
) -> float:
    """WRMSSE for one (market, fold): scale from train, weights from train tail."""
    tr = train.sort_values("date")
    origin = pd.to_datetime(tr["date"]).max()
    wstart = origin - pd.Timedelta(days=cfg.weight_window - 1)

    scales: dict[tuple, float] = {}
    weights: dict[tuple, float] = {}
    for key, g in tr.groupby(SERIES_KEY, observed=True):
        scales[key] = M.naive_scale(g[cfg.target].to_numpy())
        tail = g[pd.to_datetime(g["date"]) >= wstart]
        price = tail[cfg.price_col] if cfg.price_col in tail.columns else 1.0
        weights[key] = float((tail[cfg.target] * price).sum())

    te = test.copy()
    te["_pred"] = preds.reindex(te.index).to_numpy()
    rmsses: list[float] = []
    ws: list[float] = []
    for key, g in te.groupby(SERIES_KEY, observed=True):
        rmsses.append(
            M.rmsse(g[cfg.target].to_numpy(), g["_pred"].to_numpy(), scales.get(key, float("nan")))
        )
        ws.append(weights.get(key, 0.0))
    return M.weighted_rmsse(rmsses, ws)


def select_top_series(
    df: pd.DataFrame, n: int, per_market: bool = True, target: str = "units"
) -> pd.DataFrame:
    """Keep only the highest-volume `n` series (per market) — bounds heavy models.

    Per-series statistical / Prophet fits are O(#series); on this Mac we cap the
    series count so a smoke run stays quick, deferring full-scale fits to cloud.
    """
    group = ["market"] if per_market else []
    totals = df.groupby(group + SERIES_KEY, observed=True)[target].sum().reset_index()
    if per_market:
        keep = totals.groupby("market", group_keys=False).apply(lambda g: g.nlargest(n, target))
    else:
        keep = totals.nlargest(n, target)
    kept_keys = set(map(tuple, keep[SERIES_KEY].to_numpy()))
    mask = df[SERIES_KEY].apply(tuple, axis=1).isin(kept_keys)
    return df[mask].copy()


def evaluate(
    df: pd.DataFrame,
    forecasters: dict[str, ForecasterFactory],
    config: BacktestConfig | None = None,
) -> pd.DataFrame:
    """Run all forecasters over rolling-origin folds; return tidy results.

    Columns: `model, market, fold, metric, value`. WRMSSE is the primary metric;
    MAE/RMSE/MAPE/sMAPE/WAPE are reported alongside. A forecaster that raises is
    logged and skipped for that (market, fold) rather than killing the run.
    """
    cfg = config or BacktestConfig()
    folds = rolling_origin_splits(
        df, horizon_days=cfg.horizon, n_folds=cfg.n_folds, step_days=cfg.step_days
    )
    markets = sorted(df["market"].unique()) if cfg.per_market else ["ALL"]

    rows: list[dict] = []
    for fold_idx, split in enumerate(folds):
        for market in markets:
            if cfg.per_market:
                tr = split.train[split.train["market"] == market]
                te = split.test[split.test["market"] == market]
            else:
                tr, te = split.train, split.test
            if tr.empty or te.empty:
                continue

            for name, factory in forecasters.items():
                try:
                    model = factory()
                    model.fit(tr)
                    preds = model.predict(te)
                except Exception as exc:  # noqa: BLE001 — one bad model must not sink the run
                    logger.warning("skip %s on %s/fold%d: %s", name, market, fold_idx, exc)
                    continue

                y_true = te[cfg.target].to_numpy()
                y_pred = preds.reindex(te.index).to_numpy()
                fold_metrics = M.point_metrics(y_true, y_pred)
                fold_metrics["wrmsse"] = _group_wrmsse(tr, te, preds, cfg)
                for metric_name, value in fold_metrics.items():
                    rows.append(
                        {
                            "model": name,
                            "market": market,
                            "fold": fold_idx,
                            "metric": metric_name,
                            "value": value,
                        }
                    )

    return pd.DataFrame(rows, columns=["model", "market", "fold", "metric", "value"])
