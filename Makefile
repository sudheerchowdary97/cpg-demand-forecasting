PY ?= python3.12
VENV := .venv
BIN := $(VENV)/bin

.PHONY: setup install lint format test data eda features baselines mlp notebook clean summary task1-summary task2-summary techstack roadmap mockup report task0 help

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

setup:  ## Create the Python 3.12 venv and install everything (run once)
	$(PY) -m venv $(VENV)
	$(BIN)/pip install -U pip
	$(BIN)/pip install -e ".[dev,docs,data,baselines,neural]"
	$(BIN)/pre-commit install

install:  ## Reinstall project + dev dependencies into the existing venv
	$(BIN)/pip install -e ".[dev,docs,data,baselines,neural]"

lint:  ## Check code style without changing files
	$(BIN)/ruff check src tests
	$(BIN)/black --check src tests

format:  ## Auto-format and auto-fix lint issues
	$(BIN)/black src tests
	$(BIN)/ruff check --fix src tests

test:  ## Run the test suite
	$(BIN)/pytest

data:  ## Regenerate the full synthetic dataset (DVC-tracked)
	$(BIN)/python -m cpg_forecast.data.generator --out data/synthetic/demand.parquet
	$(BIN)/dvc add data/synthetic/demand.parquet

eda:  ## Run Task 2 EDA (figures -> docs/eda/, findings + market-wise docs/EDA.xlsx)
	$(BIN)/python -m cpg_forecast.eda
	$(BIN)/python scripts/make_eda_workbook.py

features:  ## Run Task 3 feature pipeline (writes data/processed/features_{train,val,test}.parquet)
	$(BIN)/python -m cpg_forecast.features --out data/processed/features.parquet

baselines:  ## Task 4: local baselines + eval on the SAMPLE (smoke) -> per-market leaderboard + MLflow
	$(BIN)/python -m cpg_forecast.baselines --sample --mlflow \
		--models naive,seasonal_naive,moving_average,drift --horizon 28 --n-folds 3
# Full roadmap set on the full dataset (heavy: statistical/Prophet fit per series).
# Intended for cloud, not this Mac. --top-series bounds the per-series models.
#	$(BIN)/python -m cpg_forecast.baselines --mlflow --models all --top-series 200 --horizon 28 --n-folds 3

mlp:  ## Task 5: train + backtest the global MLP on the SAMPLE (smoke) -> leaderboard + MLflow
	$(BIN)/python -m cpg_forecast.neural --sample --mlflow \
		--models mlp,seasonal_naive --horizon 28 --n-folds 3 --epochs 15
# GBM comparison (lightgbm/xgboost) segfaults with torch in one process on macOS;
# run it separately via `make baselines`, or add them here on Linux/cloud.
# Full run (all markets, bounded series) — heavier; prefer cloud GPU:
#	$(BIN)/python -m cpg_forecast.neural --mlflow --models mlp --top-series 200 --epochs 60

notebook:  ## Launch JupyterLab (opens in your default browser)
	$(BIN)/jupyter lab

summary:  ## Regenerate the Task 0 business + developer summary workbook
	$(BIN)/python scripts/make_task0_summary.py

task1-summary:  ## Regenerate the Task 1 summary workbook (docs/Task1_Summary.xlsx)
	$(BIN)/python scripts/make_task1_summary.py

task2-summary:  ## Regenerate the Task 2 summary workbook (docs/Task2_Summary.xlsx)
	$(BIN)/python scripts/make_task2_summary.py

techstack:  ## Regenerate the technology-stack workbook (docs/TechStack.xlsx)
	$(BIN)/python scripts/make_techstack.py

roadmap:  ## Regenerate the roadmap workbook (docs/Roadmap.xlsx)
	$(BIN)/python scripts/make_roadmap.py

mockup:  ## Open the Demand IQ product UI mockup in your browser
	open docs/product_mockup/index.html

report:  ## Open the Tasks 1–5 Bridge/Bricks HTML report in your browser
	open docs/tasks_1_5_report/index.html

task0:  ## Open the Task 0 report (architecture + what was done) in your browser
	open docs/task0_report/index.html

clean:  ## Remove caches and build artifacts
	rm -rf .pytest_cache .ruff_cache **/__pycache__ src/*.egg-info
