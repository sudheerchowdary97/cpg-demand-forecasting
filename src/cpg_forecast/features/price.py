"""Price & promotion features (Task 3).

EDA found promo uplift ~1.59x and holiday uplift ~1.49x — too large to leave
implicit. `discount_pct` captures magnitude (not just presence) of a promo,
complementing `promo_flag`. See docs/eda_findings.md.
"""

from __future__ import annotations

import pandas as pd


def add_price_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add discount depth and relative-price features."""
    out = df.copy()
    out["discount_pct"] = 1.0 - out["price"] / out["base_price"]
    return out
