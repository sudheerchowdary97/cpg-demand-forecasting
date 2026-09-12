"""Task 2 — Exploratory Data Analysis on the synthetic demand dataset.

Reproducible: loads data/synthetic/demand.parquet (regenerating it if missing),
computes findings, writes figures to docs/eda/, and a findings doc to
docs/eda_findings.md. Pure-compute helpers are unit-tested on a small sample.

Run with:  make eda   (or)   python -m cpg_forecast.eda
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless; no GUI on the Mac
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cpg_forecast.data import DataConfig, generate

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "synthetic" / "demand.parquet"
FIG_DIR = ROOT / "docs" / "eda"
FINDINGS = ROOT / "docs" / "eda_findings.md"

BLUE = "#004b93"


def load_data() -> pd.DataFrame:
    if DATA.exists():
        df = pd.read_parquet(DATA)
    else:
        df = generate(DataConfig())
    df["date"] = pd.to_datetime(df["date"])
    df["dow"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["hemisphere"] = np.where(df["market"] == "Australia", "Southern", "Northern")
    return df


def acf(x: np.ndarray, nlags: int) -> list[float]:
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    denom = (x * x).sum()
    return [float((x[: len(x) - k] * x[k:]).sum() / denom) for k in range(nlags + 1)]


def compute_findings(df: pd.DataFrame) -> dict:
    total = int(df["units"].sum())
    zero_pct = float((df["units"] == 0).mean() * 100)
    by_market = df.groupby("market")["units"].sum().sort_values(ascending=False)
    ch = df.groupby(["market", "channel"])["units"].sum()
    ch_share = (ch / ch.groupby(level=0).sum() * 100).round(1)
    dow = df.groupby("dow")["units"].mean()
    weekend_lift = float(dow[dow.index >= 4].mean() / dow[dow.index < 4].mean())
    promo = df.groupby("promo_flag")["units"].mean()
    promo_uplift = float(promo.get(1, np.nan) / promo.get(0, np.nan))
    hol = df.assign(is_hol=df["holiday"] != "").groupby("is_hol")["units"].mean()
    holiday_uplift = float(hol.get(True, np.nan) / hol.get(False, np.nan))
    bev = df[df["category"] == "Beverage"]
    weather_corr = {
        m: float(
            sub.groupby("date").agg(u=("units", "sum"), t=("temp_c", "mean")).corr().iloc[0, 1]
        )
        for m, sub in bev.groupby("market")
    }
    # GT share in India/Pakistan (traditional trade dominance)
    gt = {
        m: float(ch_share.loc[m].filter(like="General Trade").sum())
        for m in ("India", "Pakistan")
        if m in df["market"].unique()
    }
    return {
        "rows": len(df),
        "total_units": total,
        "zero_pct": zero_pct,
        "by_market": by_market,
        "ch_share": ch_share,
        "weekend_lift": weekend_lift,
        "promo_uplift": promo_uplift,
        "holiday_uplift": holiday_uplift,
        "weather_corr": weather_corr,
        "gt_share": gt,
    }


def make_figures(df: pd.DataFrame) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Units by market
    by_market = df.groupby("market")["units"].sum().sort_values(ascending=False)
    _bar(by_market, "Total units by market", "fig_units_by_market.png")

    # 2) Channel share of volume (stacked) per market
    ch = df.groupby(["market", "channel"])["units"].sum().unstack(fill_value=0)
    ch = ch.div(ch.sum(axis=1), axis=0) * 100
    ax = ch.plot(kind="barh", stacked=True, figsize=(9, 4), colormap="tab20")
    ax.set_title("Channel share of volume by market (%)")
    ax.legend(bbox_to_anchor=(1.01, 1), fontsize=7)
    _save("fig_channel_share.png")

    # 3) Weekly seasonality
    dow = df.groupby("dow")["units"].mean()
    dow.index = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    _bar(dow, "Weekly seasonality (mean units by weekday)", "fig_weekly.png")

    # 4) Monthly seasonality by hemisphere (the flip)
    mh = df.groupby(["hemisphere", "month"])["units"].mean().unstack(0)
    ax = mh.plot(figsize=(9, 4), marker="o")
    ax.set_title("Monthly seasonality by hemisphere (Australia is flipped)")
    ax.set_xlabel("month")
    _save("fig_seasonality_hemisphere.png")

    # 5) ACF of aggregate daily demand
    daily = df.groupby("date")["units"].sum().sort_index().to_numpy()
    vals = acf(daily, 35)
    plt.figure(figsize=(9, 3.5))
    plt.bar(range(len(vals)), vals, color=BLUE)
    plt.axhline(0, color="#999", lw=0.8)
    plt.title("Autocorrelation of daily demand (weekly spikes at 7/14/21/28)")
    plt.xlabel("lag (days)")
    _save("fig_acf.png")

    # 6) Promo & holiday uplift
    promo = df.groupby(df["promo_flag"].map({0: "No promo", 1: "Promo"}))["units"].mean()
    hol = (
        df.assign(h=np.where(df["holiday"] != "", "Holiday", "Normal")).groupby("h")["units"].mean()
    )
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5))
    promo.plot(kind="bar", ax=axes[0], color=[BLUE, "#eb1700"], title="Promotion uplift")
    hol.plot(kind="bar", ax=axes[1], color=["#999", "#12894f"], title="Holiday uplift")
    for a in axes:
        a.tick_params(axis="x", rotation=0)
    _save("fig_promo_holiday.png")

    # 7) Weather vs beverage demand (India)
    bev = df[(df["category"] == "Beverage") & (df["market"] == "India")]
    agg = bev.groupby("date").agg(u=("units", "sum"), t=("temp_c", "mean"))
    plt.figure(figsize=(6, 4))
    plt.scatter(agg["t"], agg["u"], s=6, alpha=0.4, color=BLUE)
    plt.title("Beverage demand vs temperature (India)")
    plt.xlabel("temp (C)")
    plt.ylabel("daily beverage units")
    _save("fig_weather_beverage.png")


def _bar(series: pd.Series, title: str, fname: str) -> None:
    ax = series.plot(kind="bar", figsize=(8, 4), color=BLUE)
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=30)
    _save(fname)


def _save(fname: str) -> None:
    plt.tight_layout()
    plt.savefig(FIG_DIR / fname, dpi=110, bbox_inches="tight")
    plt.close()


def write_findings(f: dict) -> None:
    lines = [
        "# EDA Findings — Task 2\n",
        "> Synthetic dataset (`data/synthetic/demand.parquet`). Figures in `docs/eda/`.\n",
        f"- **Rows:** {f['rows']:,} · **total units:** {f['total_units']:,} · "
        f"**zero-demand days:** {f['zero_pct']:.1f}% (intermittency).",
        f"- **Volume by market:** {', '.join(f'{m} {int(v):,}' for m, v in f['by_market'].items())}.",
        f"- **Traditional/General Trade share** — India {f['gt_share'].get('India', float('nan')):.0f}%, "
        f"Pakistan {f['gt_share'].get('Pakistan', float('nan')):.0f}% (dominant, as expected).",
        f"- **Weekly seasonality:** weekend demand ≈ **{f['weekend_lift']:.2f}×** weekday.",
        f"- **Promotion uplift:** ≈ **{f['promo_uplift']:.2f}×** vs non-promo.",
        f"- **Holiday uplift:** ≈ **{f['holiday_uplift']:.2f}×** vs normal days.",
        "- **Weather (beverages):** temp↔demand correlation — "
        + ", ".join(f"{m} {c:+.2f}" for m, c in f["weather_corr"].items())
        + ".",
        "- **Autocorrelation:** clear spikes at lags 7/14/21/28 → strong weekly cycle.",
        "- **Hemisphere flip:** Australia's monthly seasonality is inverted vs UK/IN/PK.\n",
        "## Modelling implications",
        "- Features must include lags/rolling stats, weekday & month, promo & holiday flags, temperature.",
        "- Channel & retailer differ sharply (volume, intermittency) → embeddings + possible channel segmentation.",
        "- Intermittent/zero-heavy SKUs need count/quantile losses (Poisson/Tweedie/pinball), not plain MSE.",
        "- Per-market seasonality differences argue for market embeddings (or per-market/segmented models).",
    ]
    FINDINGS.write_text("\n".join(lines) + "\n")


def main() -> None:
    df = load_data()
    findings = compute_findings(df)
    make_figures(df)
    write_findings(findings)
    print(
        f"EDA complete. Figures -> {FIG_DIR.relative_to(ROOT)}, findings -> {FINDINGS.relative_to(ROOT)}"
    )
    print(
        f"rows={findings['rows']:,} zero%={findings['zero_pct']:.1f} "
        f"weekend={findings['weekend_lift']:.2f}x promo={findings['promo_uplift']:.2f}x "
        f"holiday={findings['holiday_uplift']:.2f}x"
    )


if __name__ == "__main__":
    main()
