"""MLPForecaster — the Task 5 global MLP as a drop-in `Forecaster` (Task 5).

Implements the same `fit(train)->self` / `predict(test)->Series` contract as the
Task 4 baselines, so it scores on the exact same WRMSSE harness and leaderboard.
`fit` trains one global `LitMLP` across all markets (entity embeddings handle the
per-market/channel/SKU differences); `predict` is the recursive, leakage-free
rollout borrowed from the GBM baseline — day d rebuilds its `L`-day window from
actual history plus the model's own earlier predictions, so it never peeks at
test-window actuals.

Run globally via `BacktestConfig(fit_scope="global")` (see the CLI) so one shared
network is fit per fold and scored per market.
"""

from __future__ import annotations

import logging
import warnings
from pathlib import Path

import lightning as L
import numpy as np
import pandas as pd
import torch
from lightning.pytorch.callbacks import EarlyStopping
from torch.utils.data import DataLoader, TensorDataset

from cpg_forecast.baselines.base import SERIES_KEY, Baseline, register
from cpg_forecast.features.encoding import EMBEDDING_COLUMNS, CategoryEncoder
from cpg_forecast.features.lags import add_lag_features
from cpg_forecast.neural.lightning_module import LitMLP
from cpg_forecast.neural.windows import (
    CODE_COLS,
    COVARIATE_COLS,
    DEFAULT_WINDOW,
    TARGET,
    Standardizer,
    add_calendar_features,
    add_price_features,
    add_window_features,
    assemble_numeric,
    codes_matrix,
    window_cols,
)

logger = logging.getLogger(__name__)

# Keep backtest logs readable: Lightning's info tips + dataloader-worker notes
# are advisory and fire once per fold, which would drown out the leaderboard.
logging.getLogger("lightning.pytorch").setLevel(logging.WARNING)
logging.getLogger("lightning.fabric").setLevel(logging.WARNING)
warnings.filterwarnings("ignore", message=".*does not have many workers.*")
warnings.filterwarnings("ignore", message=".*LeafSpec.*")


def _tensor_ds(numeric: np.ndarray, codes: np.ndarray, y: np.ndarray) -> TensorDataset:
    return TensorDataset(
        torch.tensor(numeric, dtype=torch.float32),
        torch.tensor(codes, dtype=torch.long),
        torch.tensor(y, dtype=torch.float32),
    )


@register("mlp")
class MLPForecaster(Baseline):
    """Global feed-forward net over a flattened window + entity embeddings."""

    def __init__(
        self,
        horizon: int = 28,
        window: int = DEFAULT_WINDOW,
        hidden: tuple[int, ...] = (256, 128),
        dropout: float = 0.1,
        lr: float = 1e-3,
        weight_decay: float = 1e-5,
        batch_size: int = 1024,
        max_epochs: int = 30,
        patience: int = 5,
        val_days: int = 28,
        seed: int = 7,
    ) -> None:
        super().__init__(horizon=horizon)
        self.window = window
        self.hidden = hidden
        self.dropout = dropout
        self.lr = lr
        self.weight_decay = weight_decay
        self.batch_size = batch_size
        self.max_epochs = max_epochs
        self.patience = patience
        self.val_days = val_days
        self.seed = seed

    # ---- training ---------------------------------------------------------

    def fit(self, train: pd.DataFrame, target: str = TARGET) -> MLPForecaster:
        L.seed_everything(self.seed, workers=True)
        self.target_ = target
        self.fallback_ = float(train[target].mean())
        self.encoder_ = CategoryEncoder().fit(train)
        self.vocab_sizes_ = [self.encoder_.vocab_size(c) for c in EMBEDDING_COLUMNS]

        feats = self.encoder_.transform(add_window_features(train, self.window, target))
        feats = feats.dropna(subset=[f"{target}_lag{self.window}"])  # need a full window
        if feats.empty:
            raise ValueError("no rows with a complete window; increase history or lower --window")

        # Time-based validation tail for early stopping.
        dates = pd.to_datetime(feats["date"])
        cutoff = dates.max() - pd.Timedelta(days=self.val_days)
        tr_idx = (dates < cutoff).to_numpy()
        if not tr_idx.any() or tr_idx.all():
            tr_idx = np.ones(len(feats), dtype=bool)  # too little history → no val split
        va_idx = ~tr_idx

        numeric = assemble_numeric(feats, self.window)
        self.scaler_ = Standardizer().fit(numeric[tr_idx])
        numeric = self.scaler_.transform(numeric).astype("float32")
        codes = codes_matrix(feats)
        y = np.log1p(np.clip(feats[target].to_numpy("float64"), 0, None)).astype("float32")

        train_ds = _tensor_ds(numeric[tr_idx], codes[tr_idx], y[tr_idx])
        val_ds = _tensor_ds(numeric[va_idx], codes[va_idx], y[va_idx]) if va_idx.any() else None

        self.model_ = LitMLP(
            n_numeric=numeric.shape[1],
            vocab_sizes=self.vocab_sizes_,
            hidden=self.hidden,
            dropout=self.dropout,
            lr=self.lr,
            weight_decay=self.weight_decay,
        )
        callbacks = [EarlyStopping(monitor="val_loss", patience=self.patience)] if val_ds else []
        self.trainer_ = L.Trainer(
            max_epochs=self.max_epochs,
            accelerator="auto",
            devices=1,
            logger=False,
            enable_checkpointing=False,
            enable_progress_bar=False,
            enable_model_summary=False,
            callbacks=callbacks,
        )
        # drop_last avoids a size-1 final batch (BatchNorm needs >1), but only
        # when there's more than one full batch to keep.
        drop_last = len(train_ds) > self.batch_size
        train_loader = DataLoader(
            train_ds, batch_size=self.batch_size, shuffle=True, drop_last=drop_last
        )
        val_loader = DataLoader(val_ds, batch_size=self.batch_size) if val_ds else None
        self.trainer_.fit(self.model_, train_loader, val_loader)
        self.model_.eval()

        # Recent raw history per series, for the recursive window rebuild.
        origin = pd.to_datetime(train["date"]).max()
        cutoff_h = origin - pd.Timedelta(days=self.window + 5)
        cols = SERIES_KEY + ["date", target]
        hist = train[pd.to_datetime(train["date"]) > cutoff_h][cols].copy()
        hist["date"] = pd.to_datetime(hist["date"]).dt.normalize()
        self.history_ = hist
        return self

    def save_checkpoint(self, path: str | Path) -> None:
        """Persist the trained Lightning model (weights + hyperparameters)."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.trainer_.save_checkpoint(str(path))

    # ---- inference --------------------------------------------------------

    def _infer(self, numeric: np.ndarray, codes: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            device = self.model_.device
            nt = torch.tensor(numeric, dtype=torch.float32, device=device)
            ct = torch.tensor(codes, dtype=torch.long, device=device)
            return self.model_(nt, ct).cpu().numpy()

    def predict(self, test: pd.DataFrame) -> pd.Series:
        te = test.copy()
        te["date"] = pd.to_datetime(te["date"]).dt.normalize()

        # Covariates + codes are known for future dates (no target dependence).
        static = self.encoder_.transform(add_price_features(add_calendar_features(te)))
        static = static.set_index(SERIES_KEY + ["date"])[COVARIATE_COLS + CODE_COLS]

        history = self.history_.copy()
        preds: list[pd.DataFrame] = []
        for day in sorted(te["date"].unique()):
            drows = te[te["date"] == day][SERIES_KEY + ["date"]].copy()
            drows[self.target_] = np.nan

            work = pd.concat([history, drows], ignore_index=True)
            work = add_lag_features(
                work, target=self.target_, lags=tuple(range(1, self.window + 1)), windows=()
            )
            lag_part = work[work["date"] == day].set_index(SERIES_KEY + ["date"])[
                window_cols(self.window)
            ]
            frame = lag_part.join(static, how="left")

            numeric = self.scaler_.transform(assemble_numeric(frame, self.window)).astype("float32")
            yhat = np.clip(np.expm1(self._infer(numeric, codes_matrix(frame))), 0.0, None)

            filled = frame.reset_index()[SERIES_KEY + ["date"]].copy()
            filled[self.target_] = yhat
            preds.append(filled)
            history = pd.concat([history, filled], ignore_index=True)

        pred = pd.concat(preds, ignore_index=True).set_index(SERIES_KEY + ["date"])[self.target_]
        idx = pd.MultiIndex.from_arrays([te["store_id"], te["sku_id"], te["date"]])
        return self._finish(pred.reindex(idx).to_numpy(), test)
