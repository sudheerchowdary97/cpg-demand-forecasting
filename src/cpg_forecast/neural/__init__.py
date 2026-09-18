"""Task 5 neural models — global MLP over a flattened window + embeddings.

Importing this package registers the `mlp` forecaster in the shared baselines
registry, so it can be selected by name and scored on the same WRMSSE harness /
leaderboard as the Task 4 baselines. Torch/Lightning are imported only here (and
below), never from `cpg_forecast.baselines`, so the Task 4 CLI keeps working
without the optional `neural` dependencies.
"""

from cpg_forecast.neural.forecaster import MLPForecaster  # noqa: F401  (registers "mlp")

__all__ = ["MLPForecaster"]
