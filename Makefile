PY ?= python3.12
VENV := .venv
BIN := $(VENV)/bin

.PHONY: setup install lint format test clean summary help

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

setup:  ## Create the Python 3.12 venv and install everything (run once)
	$(PY) -m venv $(VENV)
	$(BIN)/pip install -U pip
	$(BIN)/pip install -e ".[dev,docs]"
	$(BIN)/pre-commit install

install:  ## Reinstall project + dev dependencies into the existing venv
	$(BIN)/pip install -e ".[dev,docs]"

lint:  ## Check code style without changing files
	$(BIN)/ruff check src tests
	$(BIN)/black --check src tests

format:  ## Auto-format and auto-fix lint issues
	$(BIN)/black src tests
	$(BIN)/ruff check --fix src tests

test:  ## Run the test suite
	$(BIN)/pytest

summary:  ## Regenerate the Task 0 business + developer summary workbook
	$(BIN)/python scripts/make_task0_summary.py

clean:  ## Remove caches and build artifacts
	rm -rf .pytest_cache .ruff_cache **/__pycache__ src/*.egg-info
