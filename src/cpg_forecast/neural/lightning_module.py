"""PyTorch Lightning module wrapping the Task 5 MLP.

Encapsulates the training loop (loss, optimizer, LR schedule) so the engineering
skill for this task — a clean Lightning `LightningModule` + `Trainer` — is
demonstrated once and reused by Tasks 6–9. Loss is Huber in `log1p` space:
robust to the demand spikes the EDA flagged, and the log space keeps the loss
from being dominated by high-volume SKUs. AdamW adds decoupled weight decay
(regularisation) and `ReduceLROnPlateau` anneals the LR when val loss stalls.
"""

from __future__ import annotations

import lightning as L
import torch
from torch import nn

from cpg_forecast.neural.model import EmbeddingMLP


class LitMLP(L.LightningModule):
    """Trainable wrapper: forward = EmbeddingMLP, target/pred are in log1p space."""

    def __init__(
        self,
        n_numeric: int,
        vocab_sizes: list[int],
        hidden: tuple[int, ...] = (256, 128),
        dropout: float = 0.1,
        lr: float = 1e-3,
        weight_decay: float = 1e-5,
    ) -> None:
        super().__init__()
        self.save_hyperparameters()
        self.net = EmbeddingMLP(n_numeric, vocab_sizes, hidden, dropout)
        self.loss_fn = nn.HuberLoss()

    def forward(self, numeric: torch.Tensor, codes: torch.Tensor) -> torch.Tensor:
        return self.net(numeric, codes)

    def _step(self, batch: tuple, stage: str) -> torch.Tensor:
        numeric, codes, y = batch
        loss = self.loss_fn(self(numeric, codes), y)
        self.log(f"{stage}_loss", loss, prog_bar=(stage == "val"), batch_size=y.shape[0])
        return loss

    def training_step(self, batch: tuple, _: int) -> torch.Tensor:
        return self._step(batch, "train")

    def validation_step(self, batch: tuple, _: int) -> torch.Tensor:
        return self._step(batch, "val")

    def configure_optimizers(self) -> dict:
        opt = torch.optim.AdamW(
            self.parameters(), lr=self.hparams.lr, weight_decay=self.hparams.weight_decay
        )
        sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, patience=2, factor=0.5)
        return {"optimizer": opt, "lr_scheduler": {"scheduler": sched, "monitor": "val_loss"}}
