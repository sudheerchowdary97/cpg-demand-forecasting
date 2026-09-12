# EDA Findings — Task 2

> Synthetic dataset (`data/synthetic/demand.parquet`). Figures in `docs/eda/`.

- **Rows:** 984,969 · **total units:** 17,594,912 · **zero-demand days:** 1.6% (intermittency).
- **Volume by market:** India 8,920,239, Pakistan 4,674,741, UK 2,353,762, Australia 1,646,170.
- **Traditional/General Trade share** — India 52%, Pakistan 65% (dominant, as expected).
- **Weekly seasonality:** weekend demand ≈ **1.15×** weekday.
- **Promotion uplift:** ≈ **1.59×** vs non-promo.
- **Holiday uplift:** ≈ **1.49×** vs normal days.
- **Weather (beverages):** temp↔demand correlation — Australia +0.90, India +0.88, Pakistan +0.88, UK +0.89.
- **Autocorrelation:** clear spikes at lags 7/14/21/28 → strong weekly cycle.
- **Hemisphere flip:** Australia's monthly seasonality is inverted vs UK/IN/PK.

## Modelling implications
- Features must include lags/rolling stats, weekday & month, promo & holiday flags, temperature.
- Channel & retailer differ sharply (volume, intermittency) → embeddings + possible channel segmentation.
- Intermittent/zero-heavy SKUs need count/quantile losses (Poisson/Tweedie/pinball), not plain MSE.
- Per-market seasonality differences argue for market embeddings (or per-market/segmented models).
