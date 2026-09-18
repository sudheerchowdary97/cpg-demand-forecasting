"""Calendar features (Task 3).

Weekday and month effects are the two clearest seasonal signals found in EDA
(weekend ~1.15x weekday; Australia's annual cycle inverted vs UK/IN/PK) — see
docs/eda_findings.md. Weekday/month are known ahead of the forecast horizon.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add weekday, weekend flag, month, and cyclical day-of-year encodings."""
    out = df.copy()
    date = pd.to_datetime(out["date"])
    doy = date.dt.dayofyear
    out["dow"] = date.dt.dayofweek
    out["is_weekend"] = (out["dow"] >= 4).astype(int)  # EDA: Fri/Sat/Sun bump
    out["month"] = date.dt.month
    # Cyclical encoding so day 365 is adjacent to day 1, not far from it.
    out["doy_sin"] = np.sin(2 * np.pi * doy / 365.0)
    out["doy_cos"] = np.cos(2 * np.pi * doy / 365.0)
    out["is_holiday"] = (out["holiday"] != "").astype(int)
    return out
