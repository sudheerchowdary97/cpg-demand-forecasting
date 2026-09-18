"""The MLP architecture for Task 5 — embeddings + feed-forward tower.

A global model: each categorical (market/channel/retailer/store/brand/category/
SKU) gets its own `nn.Embedding`, concatenated with the standardised numeric
window+covariate vector, then passed through a small MLP with BatchNorm +
Dropout for regularisation. Embedding dims follow the fast.ai rule of thumb
(`min(50, 1.6 * vocab^0.56)`), which keeps high-cardinality entities like SKU
compact while giving low-cardinality ones (market) enough room.
"""

from __future__ import annotations

import torch
from torch import nn


def _embedding_dim(vocab: int) -> int:
    """fast.ai heuristic: compact embeddings that scale sub-linearly with vocab."""
    return max(1, min(50, round(1.6 * vocab**0.56)))


class EmbeddingMLP(nn.Module):
    """Entity embeddings + numeric features → feed-forward regressor (scalar out)."""

    def __init__(
        self,
        n_numeric: int,
        vocab_sizes: list[int],
        hidden: tuple[int, ...] = (256, 128),
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.embeddings = nn.ModuleList([nn.Embedding(v, _embedding_dim(v)) for v in vocab_sizes])
        emb_total = sum(_embedding_dim(v) for v in vocab_sizes)

        layers: list[nn.Module] = []
        in_dim = n_numeric + emb_total
        for width in hidden:
            layers += [
                nn.Linear(in_dim, width),
                nn.BatchNorm1d(width),
                nn.ReLU(),
                nn.Dropout(dropout),
            ]
            in_dim = width
        layers.append(nn.Linear(in_dim, 1))
        self.mlp = nn.Sequential(*layers)

    def forward(self, numeric: torch.Tensor, codes: torch.Tensor) -> torch.Tensor:
        embs = [emb(codes[:, i]) for i, emb in enumerate(self.embeddings)]
        x = torch.cat([numeric, *embs], dim=1)
        return self.mlp(x).squeeze(-1)
