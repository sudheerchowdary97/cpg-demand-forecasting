"""Synthetic PepsiCo demand generator (Task 1).

Builds a channel-aware SKU x store x day dataset whose hidden data-generating
process injects trend, weekly + annual seasonality (hemisphere-aware), per-market
holidays, promotions with price elasticity, weather-driven beverage demand,
intermittency, cold-start listings, stockout censoring and irreducible noise.

The model must LEARN these; the DGP parameters are never exposed as features.

CLI:  python -m cpg_forecast.data.generator --out data/synthetic/demand.parquet
      python -m cpg_forecast.data.generator --sample
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from cpg_forecast.data import calendars, reference
from cpg_forecast.data.schema import COLUMNS, DataConfig, validate_frame


def _stable_unit(*parts: object) -> float:
    """Deterministic pseudo-random float in [0, 1) from arbitrary keys."""
    h = abs(hash(parts)) % 1_000_000
    return h / 1_000_000


def _allocate(total: int, weights: list[int]) -> list[int]:
    """Split `total` stores across channels by weight (largest-remainder)."""
    s = sum(weights)
    raw = [total * w / s for w in weights]
    floor = [int(x) for x in raw]
    rem = total - sum(floor)
    order = sorted(range(len(weights)), key=lambda i: raw[i] - floor[i], reverse=True)
    for i in order[:rem]:
        floor[i] += 1
    return floor


def build_stores(cfg: DataConfig) -> list[dict]:
    stores: list[dict] = []
    for market in cfg.markets:
        chans = reference.MARKET_CHANNELS[market]
        counts = _allocate(cfg.stores_per_market, [w for _c, _r, w in chans])
        sid = 0
        for (channel, retailers, _w), cnt in zip(chans, counts, strict=True):
            for i in range(cnt):
                stores.append(
                    {
                        "market": market,
                        "channel": channel,
                        "retailer": retailers[i % len(retailers)],
                        "store_id": f"{market[:2].upper()}-{sid:03d}",
                    }
                )
                sid += 1
    return stores


def build_catalog(cfg: DataConfig) -> list[dict]:
    skus: list[dict] = []
    for market in cfg.markets:
        for kind in ("Food", "Beverage"):
            for brand in reference.GEOS[market][kind]:
                pop = 0.6 + _stable_unit(brand, "pop") * 0.8  # brand popularity 0.6-1.4
                for pack, pfac, price in reference.PACKS[kind][: cfg.packs_per_brand]:
                    skus.append(
                        {
                            "market": market,
                            "category": kind,
                            "brand": brand,
                            "pack_size": pack,
                            "sku_id": f"{brand}-{pack}".replace(" ", ""),
                            "base_price": float(price),
                            "pack_factor": pfac,
                            "popularity": pop,
                        }
                    )
    return skus


def _temp_series(market: str, doy: np.ndarray) -> np.ndarray:
    """Seasonal daily temperature proxy (hemisphere-aware)."""
    mean = {"India": 27.0, "Pakistan": 27.0, "UK": 12.0, "Australia": 20.0}[market]
    amp = 8.0 if market in ("India", "Pakistan") else 10.0
    phase = np.pi if calendars.is_southern_hemisphere(market) else 0.0
    return mean + amp * np.sin(2 * np.pi * (doy - 80) / 365.0 + phase)


def generate(cfg: DataConfig) -> pd.DataFrame:
    dates = pd.date_range(cfg.start, cfg.end, freq="D")
    n = len(dates)
    doy = dates.dayofyear.to_numpy()
    dow = dates.dayofweek.to_numpy()
    weekend = np.where(dow >= 4, 1.15, 1.0)  # Fri/Sat/Sun bump

    stores = build_stores(cfg)
    catalog = build_catalog(cfg)

    # Per-market exogenous arrays (shared across that market's series).
    market_ctx: dict[str, dict] = {}
    for market in cfg.markets:
        hol = calendars.holiday_map(market)
        lift = np.ones(n)
        names = np.array([""] * n, dtype=object)
        for i, d in enumerate(dates.date):
            if d in hol:
                names[i], lift[i] = hol[d][0], hol[d][1]
        temp = _temp_series(market, doy)
        market_ctx[market] = {"lift": lift, "names": names, "temp": temp, "temp_mean": temp.mean()}

    cols: dict[str, list] = {c: [] for c in COLUMNS}
    si = 0
    for market in cfg.markets:
        ctx = market_ctx[market]
        m_stores = [s for s in stores if s["market"] == market]
        m_skus = [k for k in catalog if k["market"] == market]
        mscale = reference.MARKET_SCALE[market]
        for store in m_stores:
            cvol = reference.CHANNEL_VOL.get(store["channel"], 1.0)
            for sku in m_skus:
                rng = np.random.default_rng([cfg.seed, si])
                si += 1
                t = np.arange(n)

                base = 6.0 * mscale * cvol * sku["popularity"] * sku["pack_factor"]
                trend = 1.0 + rng.uniform(-0.05, 0.20) * (t / n)
                annual_amp = 0.25 if sku["category"] == "Beverage" else 0.12
                annual = 1.0 + annual_amp * np.sin(2 * np.pi * (doy - 80) / 365.0)

                # weather: beverages rise with temperature
                if sku["category"] == "Beverage":
                    weather = 1.0 + 0.015 * (ctx["temp"] - ctx["temp_mean"])
                else:
                    weather = np.ones(n)

                # promotions: 1-3 windows -> uplift + price discount
                promo_mult = np.ones(n)
                discount = np.zeros(n)
                for _ in range(rng.integers(1, 4)):
                    start = int(rng.integers(0, max(1, n - 10)))
                    length = int(rng.integers(5, 11))
                    up = rng.uniform(1.3, 1.9)
                    promo_mult[start : start + length] *= up
                    discount[start : start + length] = rng.uniform(0.1, 0.3)

                mean = base * trend * weekend * annual * weather * ctx["lift"] * promo_mult
                mean = np.clip(mean, 0.02, None)
                units = rng.poisson(mean).astype(float)

                # stockout censoring (~1% of days) -> zero
                units[rng.random(n) < 0.01] = 0.0

                # cold-start listing: 15% of series start partway through
                listing = 0
                if rng.random() < 0.15:
                    listing = int(rng.integers(int(n * 0.2), int(n * 0.6)))
                keep = slice(listing, n)
                k = n - listing

                price = sku["base_price"] * (1.0 - discount)
                cols["date"].extend(dates[keep])
                cols["market"].extend([market] * k)
                cols["channel"].extend([store["channel"]] * k)
                cols["retailer"].extend([store["retailer"]] * k)
                cols["store_id"].extend([store["store_id"]] * k)
                cols["category"].extend([sku["category"]] * k)
                cols["brand"].extend([sku["brand"]] * k)
                cols["sku_id"].extend([sku["sku_id"]] * k)
                cols["pack_size"].extend([sku["pack_size"]] * k)
                cols["base_price"].extend([sku["base_price"]] * k)
                cols["price"].extend(np.round(price[keep], 2))
                cols["promo_flag"].extend((discount[keep] > 0).astype(int))
                cols["holiday"].extend(ctx["names"][keep])
                cols["temp_c"].extend(np.round(ctx["temp"][keep], 1))
                cols["units"].extend(units[keep].astype(int))

    df = pd.DataFrame(cols, columns=COLUMNS)
    validate_frame(df)
    return df


def summarize(df: pd.DataFrame) -> str:
    n_series = df.groupby(["market", "store_id", "sku_id"], observed=True).ngroups
    return (
        f"rows={len(df):,} | series={n_series:,} | markets={df['market'].nunique()} | "
        f"channels={df['channel'].nunique()} | stores={df['store_id'].nunique()} | "
        f"skus={df['sku_id'].nunique()} | dates {df['date'].min().date()}..{df['date'].max().date()} | "
        f"units: mean={df['units'].mean():.2f} zero%={100 * (df['units'] == 0).mean():.1f}"
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Generate synthetic PepsiCo demand data.")
    p.add_argument("--out", default="data/synthetic/demand.parquet")
    p.add_argument("--sample", action="store_true", help="tiny fast dataset for dev/tests")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--stores", type=int)
    p.add_argument("--packs", type=int)
    args = p.parse_args()

    cfg = DataConfig.sample() if args.sample else DataConfig()
    if args.seed is not None:
        cfg.seed = args.seed
    if args.start:
        cfg.start = args.start
    if args.end:
        cfg.end = args.end
    if args.stores:
        cfg.stores_per_market = args.stores
    if args.packs:
        cfg.packs_per_brand = args.packs

    df = generate(cfg)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Wrote {out}  ({out.stat().st_size / 1e6:.1f} MB)")
    print(summarize(df))


if __name__ == "__main__":
    main()
