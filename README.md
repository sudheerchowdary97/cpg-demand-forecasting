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
make help      # list all targets
```

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
| 4 | Classical baselines & eval harness | why baselines matter | WRMSSE, backtesting, tracking |
| 5 | MLP forecaster | MLPs, backprop, regularization | Lightning training loop |
| 6 | RNN → LSTM → GRU | recurrence, gating | GPU training discipline |
| 7 | Seq2Seq + Attention | attention, multi-horizon | attention viz |
| 8 | Temporal Conv Nets (TCN) | dilated causal conv | architecture ablation |
| 9 | Transformer / TFT | self-attention, interpretability | large-model training |
| 10 | Probabilistic (DeepAR / N-BEATS / quantiles) | uncertainty, intermittency | calibration |
| 11 | Tracking, HPO & model selection | HPO, bias/variance | Optuna + MLflow |
| 12 | Cloud full-scale training | mixed precision, checkpointing | training-as-code |
| 13 | Export & optimize (ONNX / quantize) | graph export, quantization | perf benchmarking |
| 14 | Serving API (FastAPI + Docker) | inference-time preprocessing | API design, containers |
| 15 | Cloud deploy + CI/CD | production readiness | Cloud Run/Render, GitHub Actions |
| 16 | Monitoring, drift & retraining | distribution shift | observability |
| 17 | Demo app + LLM insight layer | communicating uncertainty | Streamlit, prompt design |
| 18 | Docs, presentation & portfolio | synthesis | technical writing, Keynote-HTML deck |

**Status:** Task 0 complete. Each task is committed and pushed on completion.
