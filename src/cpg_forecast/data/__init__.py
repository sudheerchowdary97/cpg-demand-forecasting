"""Synthetic demand data generation (Task 1)."""

from cpg_forecast.data.generator import generate, summarize
from cpg_forecast.data.schema import COLUMNS, DataConfig, validate_frame

__all__ = ["generate", "summarize", "COLUMNS", "DataConfig", "validate_frame"]
