"""Canonical data schema + generation config for the synthetic dataset (Task 1).

The dataset is a long-format fact table at the base grain SKU x store x day, with
the hierarchy geography -> channel -> retailer -> store -> SKU. Channel and
retailer are static store attributes (future model embeddings), NOT a flat field.
"""

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel, Field

# Canonical columns (order matters for the written Parquet).
COLUMNS: list[str] = [
    "date",  # daily timestamp
    "market",  # geography (UK / Australia / India / Pakistan)
    "channel",  # route-to-market (General Trade, Modern Trade, ...)
    "retailer",  # banner (DMart, Tesco, Kirana Store, ...)
    "store_id",  # individual outlet
    "category",  # Food / Beverage
    "brand",  # Pepsi, Lay's, ...
    "sku_id",  # brand + pack
    "pack_size",  # e.g. 330ml Can, 45g
    "base_price",  # list price (local currency units)
    "price",  # actual price on the day (promo-adjusted)
    "promo_flag",  # 1 if on promotion
    "holiday",  # holiday/festival name or "" (exogenous, known-future)
    "temp_c",  # daily temperature proxy (exogenous)
    "units",  # TARGET: units sold that day
]

NUMERIC = ["base_price", "price", "temp_c", "units", "promo_flag"]


class DataConfig(BaseModel):
    """Knobs for the synthetic generator (all overridable from the CLI)."""

    start: str = "2022-01-01"
    end: str = "2024-12-31"
    markets: list[str] = Field(default_factory=lambda: ["UK", "Australia", "India", "Pakistan"])
    stores_per_market: int = 12
    packs_per_brand: int = 2
    seed: int = 7

    @classmethod
    def sample(cls) -> DataConfig:
        """A tiny, fast configuration for tests and dev smoke-runs."""
        return cls(
            start="2023-01-01",
            end="2023-06-30",
            markets=["India"],
            stores_per_market=3,
            packs_per_brand=1,
            seed=7,
        )


def validate_frame(df: pd.DataFrame) -> None:
    """Fail loudly if the generated frame violates the contract."""
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    if df.empty:
        raise ValueError("generated frame is empty")
    if df["units"].isna().any():
        raise ValueError("units contains NaN")
    if (df["units"] < 0).any():
        raise ValueError("units has negative values")
    if (df["price"] <= 0).any():
        raise ValueError("price must be positive")
