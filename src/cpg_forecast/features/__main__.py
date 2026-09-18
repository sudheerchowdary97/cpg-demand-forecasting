"""CLI entrypoint for the Task 3 feature pipeline.

Run with:  python -m cpg_forecast.features --out data/processed/features.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

from cpg_forecast.data import DataConfig, generate
from cpg_forecast.features.pipeline import build_dataset


def main() -> None:
    p = argparse.ArgumentParser(description="Build the Task 3 feature pipeline.")
    p.add_argument("--out", default="data/processed/features.parquet")
    p.add_argument("--sample", action="store_true", help="use the tiny dev/test dataset")
    p.add_argument("--val-days", type=int, default=28)
    p.add_argument("--test-days", type=int, default=28)
    args = p.parse_args()

    cfg = DataConfig.sample() if args.sample else DataConfig()
    df = generate(cfg)
    train, val, test, _encoder = build_dataset(df, val_days=args.val_days, test_days=args.test_days)

    for name, split_df in (("train", train), ("val", val), ("test", test)):
        split_df = split_df.assign(split=name)
        out = Path(args.out).with_stem(f"{Path(args.out).stem}_{name}")
        out.parent.mkdir(parents=True, exist_ok=True)
        split_df.to_parquet(out, index=False)
        print(f"Wrote {out}  ({len(split_df):,} rows)")


if __name__ == "__main__":
    main()
