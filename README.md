# CPG Demand Forecasting — Deep Learning, End to End

Learn the **full time-series deep-learning ladder** by solving a real Consumer
Packaged Goods (CPG) pain point: **SKU × store × day demand forecasting**.
Poor forecasts cause *stockouts* (lost sales) and *overstock* (waste/markdowns) —
better forecasts drive replenishment, production, and promotion planning.

Dataset: **M5 Forecasting – Accuracy** (Walmart, via Kaggle) — 42,840 hierarchical
daily series with prices, calendar, and SNAP/holiday events.

> **Learning project.** The goal is to understand every concept, not just ship a
> number. Each task teaches one modeling idea *and* one engineering skill.

---

## Guardrails

- **No Apple ecosystem.** Public/generic tooling only; code lives on personal
  GitHub (`github.com/sudheerchowdary97`).
- **Heavy compute never runs on this Mac.** The laptop is for coding, EDA on
  samples, classical baselines, and small smoke-tests. All full-scale training
  runs on **non-Apple cloud GPU** (Kaggle / Colab).
- **Deployment** targets a real non-Apple cloud endpoint (Cloud Run / Render).
- **Python 3.12** (ML wheels don't support 3.14 yet).

---

## Quick start

```bash
make setup     # create .venv on Python 3.12 + install deps + git hooks
make test      # run smoke tests (should pass)
make lint      # ruff + black checks
make format    # auto-format + auto-fix
make summary   # regenerate the PepsiCo-styled Task 0 Excel summary
make mockup    # open the Demand IQ product UI mockup in a browser
make help      # list all targets
```

## What the end product looks like

See the interactive **[Demand IQ product mockup](docs/product_mockup/)** — a PepsiCo-styled
demand-planner console (KPIs, 28-day forecast with confidence bands, stockout/overstock
alerts, replenishment watchlist) that previews the business-facing deliverable (Task 17).
Open it with `make mockup` or `open docs/product_mockup/index.html`.

For a summary of Task 0 (architecture + what was done), see the
**[Task 0 report](docs/task0_report/)** — `make task0`.

---

## Project layout

```
deep_learning_cpg/
├── src/cpg_forecast/   # library code (installed as a package)
├── tests/              # pytest suite
├── notebooks/          # EDA / experiments
├── configs/            # experiment + pipeline configs
├── data/               # raw / interim / processed (DVC-tracked, git-ignored)
├── models/             # trained artifacts (git-ignored)
├── docs/               # specs, findings, model-evolution write-ups
├── pyproject.toml      # single source of truth for deps + tooling
├── Makefile            # one-command workflows
└── .pre-commit-config.yaml
```

---

## Roadmap (Task 0 → 18)

| # | Task | Core DL concept | Engineering skill |
|---|------|-----------------|-------------------|
| 0 | **Foundations & environment** | — | repo layout, venv, linting, CI-ready |
| 1 | Problem framing & data (DVC) | forecast task formulation | data versioning |
| 2 | EDA & time-series understanding | seasonality, stationarity | reproducible notebooks |
| 3 | Data pipeline & feature engineering | windowing, embeddings | leakage-free ETL as code |
| 4 | Local baselines & eval harness | local per-market baselines = the bar | WRMSSE, market-level backtesting, tracking |
| 5 | MLP forecaster | MLPs, backprop, regularization | Lightning training loop |
| 6 | RNN → LSTM → GRU | recurrence, gating | GPU training discipline |
| 7 | Seq2Seq + Attention | attention, multi-horizon | attention viz |
| 8 | Temporal Conv Nets (TCN) | dilated causal conv | architecture ablation |
| 9 | Transformer / TFT (global model) | self-attention + entity embeddings; global vs local per market | large-model training, market comparison |
| 10 | Probabilistic (DeepAR / N-BEATS / quantiles) | uncertainty, intermittency | calibration |
| 11 | Tracking, HPO & model selection | HPO, bias/variance | Optuna + MLflow |
| 12 | Cloud training + hybrid refinement | segmented globals, geo fine-tuning, reconciliation | training-as-code, architecture chosen by backtest |
| 13 | Export & optimize (ONNX / quantize) | graph export, quantization | perf benchmarking |
| 14 | Serving API (FastAPI + Docker) | inference-time preprocessing | API design, containers |
| 15 | Cloud deploy + CI/CD | production readiness | Cloud Run/Render, GitHub Actions |
| 16 | Monitoring, drift & retraining | distribution shift | observability |
| 17 | Demo app + LLM insight layer | communicating uncertainty | Streamlit, prompt design |
| 18 | Docs, presentation & portfolio | synthesis | technical writing, Keynote-HTML deck |

**Status:** Tasks 0–1 complete (scaffold + synthetic data generator); Task 2 (EDA) next. Each task is committed and pushed on completion.

---

## Architecture — Local vs Global vs Hybrid (evidence-driven)

We do **not** assume a single global model is the answer. The learning path is:

**Local baseline → Global model → Market-level comparison → Hybrid refinement.**

**Forecast grain & hierarchy:** base series = `SKU × store × day`, with the hierarchy
`geography → channel (route-to-market) → retailer/banner → store → SKU`. Channel and
retailer are **static store attributes** (embeddings) — not one flat "retailer" field.
Channels differ sharply (traditional trade / kirana dominates volume in India & Pakistan
with **no POS data**; modern trade, convenience, e-commerce, q-commerce, wholesale and
HoReCa each have distinct pack mix, promos, volatility, and data availability).

- **Local baselines** (Task 4) — per-market classical models; the bar every deep model must beat.
- **Global multi-series model** (Tasks 5–9) — one shared network conditioned on
  market / channel / retailer / store / brand / category / SKU **embeddings** + local covariates;
  enables cold-start for new SKUs/stores/markets.
- **Hybrid refinement** (Task 12) — **segmented global models** where useful (e.g. Beverages
  vs Snacks, or traditional vs modern trade), optional **geography fine-tuning / adapters**,
  and **hierarchical reconciliation**.
- **Selection by backtesting** — market-level rolling-origin WRMSSE decides how much pooling
  helps. A global model is *not* assumed to outperform local; the project proves it empirically.

**Data residency.** For this learning project, cross-border pooling is **allowed** because we use
the public **M5 (Walmart) proxy** dataset — the priority is understanding the modeling concepts.
In a **real PepsiCo deployment**, raw data may be legally required to stay within region/country
(e.g. India's DPDP Act); that would push the design toward **region-segmented global models,
local fine-tuning, or federated learning** depending on legal requirements.
