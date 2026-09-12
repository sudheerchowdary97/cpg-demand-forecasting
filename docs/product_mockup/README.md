# Demand IQ — Product UI Mockup

A **sample of the end-goal product** a PepsiCo demand planner would use — the
business-facing deliverable this project builds toward (Task 17 in the roadmap).

> **Mockup only.** Self-contained HTML/CSS/JS with **synthetic** data (seeded,
> generated in-browser). Not connected to a real model yet. Independent learning
> project — not affiliated with or endorsed by PepsiCo; figures are illustrative,
> based on the public M5 (Walmart) proxy, not real PepsiCo data.

## How to view

```bash
open docs/product_mockup/index.html      # macOS (or: make mockup)
# or serve it:
python -m http.server -d docs/product_mockup 8000   # then open http://localhost:8000
```

## What it shows
- **Filters:** market (UK / Australia / India / Pakistan), category (Beverages / Snacks),
  brand, forecast horizon — everything re-renders live.
- **KPI strip:** forecast accuracy (MAPE / WRMSSE), service level, projected stockouts,
  overstock/waste risk, forecast volume, on-shelf availability.
- **Forecast chart:** 90-day actuals + forecast with a **90% confidence band** and
  promotion markers; hover for values.
- **Replenishment watchlist:** top SKUs by risk with recommended actions.
- **Alerts, forecast-by-brand, promotion impact, accuracy trend, and a model/data card**
  (champion = TFT, architecture chosen by backtest, calibrated intervals).

## Why it exists now
To align on the **end goal** before building the pipeline: it makes the business value
tangible (what the planner sees) and anchors the modeling work (intervals, per-SKU
risk, per-market views) to a concrete UI.
