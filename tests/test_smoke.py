"""Smoke tests for Task 0.

These prove the package is importable and the toolchain runs green before we
add any real forecasting code. Nothing here should ever be heavy.
"""

import cpg_forecast


def test_package_imports():
    assert cpg_forecast is not None


def test_version_is_set():
    assert cpg_forecast.__version__ == "0.1.0"
