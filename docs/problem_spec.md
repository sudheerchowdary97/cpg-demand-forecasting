# Problem Spec — PepsiCo Demand Forecasting (Task 1)

> Independent learning project. NOT affiliated with or endorsed by PepsiCo.
> Data is **synthetic** (generated locally); a real engagement would use PepsiCo
> shipment / POS / Nielsen data per market.

## Business problem
Forecast product demand accurately at store level so the right pack is on the
right shelf at the right time — reducing **stockouts** (lost sales) and
**overstock/waste** (markdowns, spoilage) across markets and channels.

## Prediction task
- **Target:** `units` sold, per **SKU × store × day**.
- **Horizon:** 28 days ahead.
- **Grain / hierarchy:** `geography → channel → retailer → store → SKU × day`.
  Channel and retailer are **static store attributes** (future model embeddings).
- **Outputs:** point forecast **and** prediction intervals (probabilistic).

## Metrics
- **Primary:** WRMSSE (M5 competition metric).
- **Supporting:** MAE, RMSE, MAPE, sMAPE, WAPE; pinball loss + interval coverage
  for probabilistic forecasts.
- **Evaluation:** rolling-origin backtesting, reported **per market**.

## Dataset (synthetic, this task)
Long-format Parquet at `data/synthetic/demand.parquet` (git-ignored; DVC-tracked).

Full config (default): **~991K rows · 960 series · 4 markets · 10 channels ·
48 stores · 40 SKUs · 3 years (2022–2024)**. Regenerate:

```bash
python -m cpg_forecast.data.generator                 # full
python -m cpg_forecast.data.generator --sample        # tiny, for dev/tests
```

### Columns
`date, market, channel, retailer, store_id, category, brand, sku_id, pack_size,
base_price, price, promo_flag, holiday, temp_c, units`

## What the hidden DGP injects (the model must LEARN these)
Trend · weekly + annual seasonality · **hemisphere flip** (Australia) ·
per-market **holidays/festivals** (Diwali, Eid, Christmas…) · **promotions + price
discounts** · **weather-driven** beverage demand · **intermittency** (sparse slow
SKUs) · **cold-start** listings (new SKUs start partway) · **stockout censoring**
(zeros) · channel effects (GT vs MT vs wholesale pack/volume) · irreducible noise.

DGP parameters are **never** exposed as features — only observable covariates are.
Because we control the DGP, we know the **irreducible noise floor** and can measure
how close each model gets to it.

## Scope boundaries
- Retail sell-through only (HoReCa/on-premise excluded from the store dataset).
- Illustrative 4 markets (extensible); cross-border pooling allowed (synthetic).
- Architecture (local vs global vs hybrid) is decided later by **backtesting**,
  not assumed here.
