"""Categorical encoding prep for embeddings (Task 3).

EDA found channel mix and volume differ sharply by market (GT-dominant
India/Pakistan vs MT-dominant UK/Australia) and per-market seasonality
differs (hemisphere flip) — see docs/eda_findings.md. Rather than one-hot
encoding (which would explode dimensionality and can't share statistical
strength across categories), we assign each categorical column a stable
integer code so Task 5+ models can look it up in an nn.Embedding table.

Codes are fit once on the training split and reused for val/test so an
unseen category at inference time maps to a reserved "unknown" index instead
of crashing or silently shifting other codes.
"""

from __future__ import annotations

import pandas as pd

EMBEDDING_COLUMNS = ["market", "channel", "retailer", "category", "brand", "sku_id", "store_id"]
UNKNOWN_CODE = 0


class CategoryEncoder:
    """Fits integer vocabularies on a training frame, applies them elsewhere."""

    def __init__(self, columns: list[str] = EMBEDDING_COLUMNS) -> None:
        self.columns = columns
        self.vocabs: dict[str, dict[str, int]] = {}

    def fit(self, df: pd.DataFrame) -> CategoryEncoder:
        for col in self.columns:
            categories = sorted(df[col].dropna().unique())
            # 0 is reserved for "unknown" (categories unseen at fit time).
            self.vocabs[col] = {cat: i + 1 for i, cat in enumerate(categories)}
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        for col in self.columns:
            vocab = self.vocabs[col]
            out[f"{col}_code"] = out[col].map(vocab).fillna(UNKNOWN_CODE).astype(int)
        return out

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.fit(df).transform(df)

    def vocab_size(self, col: str) -> int:
        """Size of the embedding table needed for this column (+1 for unknown)."""
        return len(self.vocabs[col]) + 1
