"""Walk-forward backtesting for Prophet demand predictions."""

from __future__ import annotations

import os
import sys
from typing import Any

import pandas as pd

# analytical-model and repo `services` root
_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_ROOT, "..", "analytical-model"))
sys.path.insert(0, os.path.join(_ROOT, ".."))

from prophet_model import (  # noqa: E402
    MIN_DATAPOINTS,
    VALID_BOROUGHS,
    build_prophet_dataframe,
    fit_and_forecast,
    get_time_of_day_factor,
    get_weather_multiplier,
    normalise_to_index,
)
from data_sampler import load_merged_records_for_borough  # noqa: E402
from metrics import calculate_accuracy, calculate_mae, calculate_rmse  # noqa: E402

TRAIN_FRACTION = 0.8
ACCURACY_TOLERANCE = 15.0
ACCURACY_THRESHOLD = 80.0


def _trip_to_demand_proxy(trip_count: float, train_trips: list[float]) -> float:
    """Min–max scale trip_count to 0–100 using training-window trip counts only."""
    if not train_trips:
        return 50.0
    tmin, tmax = min(train_trips), max(train_trips)
    if tmax == tmin:
        return 50.0
    v = ((float(trip_count) - tmin) / (tmax - tmin)) * 100.0
    return round(max(0.0, min(100.0, v)), 1)


def _predictions_for_test_period(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    *,
    use_regressors: bool,
) -> list[float]:
    """Return crowd demand index (0–100) per test row, aligned with ``test_df`` order."""
    if test_df.empty or train_df.empty:
        return []

    forecast_start = test_df["ds"].min().strftime("%Y-%m-%d")
    forecast_end = test_df["ds"].max().strftime("%Y-%m-%d")
    hist_y = train_df["y"].tolist()
    tod = get_time_of_day_factor("all")

    if use_regressors:
        future_regs = test_df[["ds", "event_count", "is_rainy", "temperature_c"]].copy()
        forecast = fit_and_forecast(
            train_df,
            forecast_start,
            forecast_end,
            use_regressors=True,
            future_regressors=future_regs,
        )
    else:
        forecast = fit_and_forecast(
            train_df,
            forecast_start,
            forecast_end,
            use_regressors=False,
        )

    forecast = forecast.sort_values("ds").reset_index(drop=True)
    test_df = test_df.sort_values("ds").reset_index(drop=True)
    yhat = forecast["yhat"].tolist()

    out: list[float] = []
    for i in range(len(test_df)):
        n_mid = normalise_to_index([yhat[i]], hist_y)[0]
        weather = str(test_df["dominant_weather"].iloc[i])
        wmult = get_weather_multiplier(weather)
        raw = n_mid * tod * wmult
        adj = max(0.0, min(100.0, round(raw, 1)))
        out.append(adj)
    return out


def run_borough_backtest(bucket: str, borough: str) -> dict[str, Any]:
    """Run 80/20 date split backtest for one borough; returns metrics and demand_proxy ground truth."""
    records = load_merged_records_for_borough(bucket, borough)
    dates = sorted({r.get("date", "") for r in records if r.get("date")})

    err: dict[str, Any] = {
        "accuracy": 0.0,
        "mae": 0.0,
        "rmse": 0.0,
        "pass": False,
        "error": "",
        "n_train": 0,
        "n_test": 0,
    }

    if len(dates) < MIN_DATAPOINTS + 2:
        err["error"] = f"Not enough distinct dates ({len(dates)}); need more than {MIN_DATAPOINTS + 1}."
        return err

    split_idx = max(MIN_DATAPOINTS, int(len(dates) * TRAIN_FRACTION))
    if split_idx >= len(dates):
        err["error"] = "Train/test split leaves no hold-out dates."
        return err

    train_dates = set(dates[:split_idx])
    test_dates = dates[split_idx:]
    train_records = [r for r in records if r.get("date") in train_dates]
    test_records = [r for r in records if r.get("date") in test_dates]

    train_df = build_prophet_dataframe(train_records)
    test_df = build_prophet_dataframe(test_records)

    if len(train_df) < MIN_DATAPOINTS or test_df.empty:
        err["error"] = "Insufficient rows after dataframe build."
        return err

    train_trips = train_df["y"].tolist()
    preds = _predictions_for_test_period(train_df, test_df, use_regressors=True)
    if len(preds) != len(test_df):
        err["error"] = "Forecast length mismatch."
        return err

    actuals = [_trip_to_demand_proxy(float(test_df["y"].iloc[i]), train_trips) for i in range(len(test_df))]

    acc = calculate_accuracy(actuals, preds, ACCURACY_TOLERANCE)
    mae = calculate_mae(actuals, preds)
    rmse = calculate_rmse(actuals, preds)

    return {
        "accuracy": acc,
        "mae": mae,
        "rmse": rmse,
        "pass": acc >= ACCURACY_THRESHOLD,
        "n_train": len(train_df),
        "n_test": len(test_df),
        "actuals": actuals,
        "predicted": preds,
        "error": "",
    }


def run_walk_forward_backtest(
    bucket: str,
    boroughs: list[str] | None = None,
) -> dict[str, Any]:
    """Backtest all boroughs (or a subset); overall accuracy is the mean of per-borough accuracies."""
    target_boroughs = sorted(boroughs) if boroughs else sorted(VALID_BOROUGHS)
    borough_results: dict[str, Any] = {}
    accums: list[float] = []

    for b in target_boroughs:
        res = run_borough_backtest(bucket, b)
        borough_results[b] = {k: v for k, v in res.items() if k not in ("actuals", "predicted")}
        if res.get("error"):
            borough_results[b]["pass"] = False
        accums.append(float(res.get("accuracy", 0.0)))

    overall = round(sum(accums) / len(accums), 2) if accums else 0.0
    return {
        "borough_results": borough_results,
        "overall_accuracy": overall,
        "overall_pass": overall >= ACCURACY_THRESHOLD,
        "threshold": ACCURACY_THRESHOLD,
        "tolerance": ACCURACY_TOLERANCE,
    }


def run_regressor_comparison(bucket: str, borough: str) -> dict[str, Any]:
    """Compare baseline Prophet (no regressors) vs full model on the same hold-out split."""
    records = load_merged_records_for_borough(bucket, borough)
    dates = sorted({r.get("date", "") for r in records if r.get("date")})
    if len(dates) < MIN_DATAPOINTS + 2:
        return {
            "baseline_accuracy": 0.0,
            "full_model_accuracy": 0.0,
            "improvement": 0.0,
            "regressors_add_value": False,
            "pass": False,
            "error": "Insufficient dates for regressor comparison.",
        }

    split_idx = max(MIN_DATAPOINTS, int(len(dates) * TRAIN_FRACTION))
    train_dates = set(dates[:split_idx])
    test_dates = dates[split_idx:]
    train_records = [r for r in records if r.get("date") in train_dates]
    test_records = [r for r in records if r.get("date") in test_dates]
    train_df = build_prophet_dataframe(train_records)
    test_df = build_prophet_dataframe(test_records)
    if len(train_df) < MIN_DATAPOINTS or test_df.empty:
        return {
            "baseline_accuracy": 0.0,
            "full_model_accuracy": 0.0,
            "improvement": 0.0,
            "regressors_add_value": False,
            "pass": False,
            "error": "Insufficient rows for regressor comparison.",
        }

    train_trips = train_df["y"].tolist()
    actuals = [_trip_to_demand_proxy(float(test_df["y"].iloc[i]), train_trips) for i in range(len(test_df))]

    preds_full = _predictions_for_test_period(train_df, test_df, use_regressors=True)
    preds_base = _predictions_for_test_period(train_df, test_df, use_regressors=False)
    if len(preds_full) != len(actuals) or len(preds_base) != len(actuals):
        return {
            "baseline_accuracy": 0.0,
            "full_model_accuracy": 0.0,
            "improvement": 0.0,
            "regressors_add_value": False,
            "pass": False,
            "error": "Forecast length mismatch in regressor comparison.",
        }

    acc_b = calculate_accuracy(actuals, preds_base, ACCURACY_TOLERANCE)
    acc_f = calculate_accuracy(actuals, preds_full, ACCURACY_TOLERANCE)
    imp = round(acc_f - acc_b, 2)
    return {
        "baseline_accuracy": acc_b,
        "full_model_accuracy": acc_f,
        "improvement": imp,
        "regressors_add_value": imp >= 3.0,
        "pass": imp >= 3.0,
        "borough": borough,
        "error": "",
    }
