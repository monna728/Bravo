"""Scoring helpers for analytical model evaluation."""

from __future__ import annotations

import math
from typing import Any


def calculate_accuracy(actual: list[float], predicted: list[float], tolerance: float = 15.0) -> float:
    """Percentage of predictions within ±``tolerance`` of the actual value (target ≥ 80%)."""
    if not actual or len(actual) != len(predicted):
        return 0.0
    hits = sum(1 for a, p in zip(actual, predicted) if abs(float(a) - float(p)) <= tolerance)
    return round(100.0 * hits / len(actual), 2)


def calculate_mae(actual: list[float], predicted: list[float]) -> float:
    """Mean absolute error between predicted and actual."""
    if not actual or len(actual) != len(predicted):
        return 0.0
    return round(sum(abs(float(a) - float(p)) for a, p in zip(actual, predicted)) / len(actual), 4)


def calculate_rmse(actual: list[float], predicted: list[float]) -> float:
    """Root mean square error (penalises large errors)."""
    if not actual or len(actual) != len(predicted):
        return 0.0
    mse = sum((float(a) - float(p)) ** 2 for a, p in zip(actual, predicted)) / len(actual)
    return round(math.sqrt(mse), 4)


def calculate_mape(actual: list[float], predicted: list[float]) -> float:
    """Mean absolute percentage error; skips days where actual is ~0."""
    if not actual or len(actual) != len(predicted):
        return 0.0
    terms: list[float] = []
    for a, p in zip(actual, predicted):
        af = float(a)
        if abs(af) < 1e-9:
            continue
        terms.append(abs((af - float(p)) / af) * 100.0)
    return round(sum(terms) / len(terms), 4) if terms else 0.0


def calculate_directional_accuracy(actual: list[float], predicted: list[float]) -> float:
    """Share of steps where predicted and actual demand move in the same direction (target ≥ 70%)."""
    if len(actual) < 2 or len(predicted) < 2:
        return 100.0
    correct = 0
    total = 0
    for i in range(1, len(actual)):
        da = float(actual[i]) - float(actual[i - 1])
        dp = float(predicted[i]) - float(predicted[i - 1])
        total += 1
        if da == 0.0 and dp == 0.0:
            correct += 1
        elif da != 0.0 and dp != 0.0 and (da > 0) == (dp > 0):
            correct += 1
    return round(100.0 * correct / total, 2) if total else 100.0


def score_summary(actual: list[float], predicted: list[float]) -> dict[str, Any]:
    """Compute all metrics and boolean pass flags against default thresholds."""
    acc = calculate_accuracy(actual, predicted)
    mae = calculate_mae(actual, predicted)
    rmse = calculate_rmse(actual, predicted)
    mape = calculate_mape(actual, predicted)
    dir_acc = calculate_directional_accuracy(actual, predicted)
    return {
        "accuracy": acc,
        "accuracy_pass": acc >= 80.0,
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "directional_accuracy": dir_acc,
        "directional_pass": dir_acc >= 70.0,
    }
