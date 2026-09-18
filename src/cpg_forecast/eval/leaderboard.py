"""Leaderboard aggregation + persistence (Task 4).

Turns the tidy backtest results into the deliverable "Leaderboard v1": mean
metric per (model, market) across folds, plus an `overall` column.

`overall` is the **mean of per-market WRMSSE**, not a pooled global WRMSSE, on
purpose: prices are in each market's local currency, so summing dollar-sales
weights across UK/India/etc. would mix currencies and be meaningless. Each
market is normalised internally, then averaged.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PRIMARY_METRIC = "wrmsse"


def build_leaderboard(results: pd.DataFrame) -> pd.DataFrame:
    """Mean over folds → one row per (model, market, metric)."""
    if results.empty:
        return results.copy()
    return (
        results.groupby(["model", "market", "metric"], as_index=False)["value"]
        .mean()
        .sort_values(["metric", "market", "value"])
        .reset_index(drop=True)
    )


def leaderboard_pivot(leaderboard: pd.DataFrame, metric: str = PRIMARY_METRIC) -> pd.DataFrame:
    """Wide model×market table for one metric, with an `overall` mean column.

    Rows are sorted best-first by `overall` (lower is better for all our error
    metrics), so the top row is the baseline bar Task 5+ must beat.
    """
    sub = leaderboard[leaderboard["metric"] == metric]
    if sub.empty:
        return sub
    wide = sub.pivot(index="model", columns="market", values="value")
    wide["overall"] = wide.mean(axis=1)
    return wide.sort_values("overall")


def write_leaderboard(
    results: pd.DataFrame,
    out_dir: str | Path = "models/leaderboards",
    stem: str = "task4_leaderboard",
    metric: str = PRIMARY_METRIC,
) -> dict[str, Path]:
    """Persist the tidy leaderboard (parquet+csv) and the primary-metric pivot."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    board = build_leaderboard(results)
    pivot = leaderboard_pivot(board, metric=metric)

    paths = {
        "parquet": out / f"{stem}.parquet",
        "csv": out / f"{stem}.csv",
        "pivot_csv": out / f"{stem}_{metric}_by_market.csv",
    }
    board.to_parquet(paths["parquet"], index=False)
    board.to_csv(paths["csv"], index=False)
    pivot.to_csv(paths["pivot_csv"])
    return paths
