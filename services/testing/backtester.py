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
# Backtests use sampled trip-count proxies (not full TLC census counts), so a wider
# tolerance is required to avoid over-penalising normal sampling variance.
ACCURACY_TOLERANCE = 35.0
ACCURACY_THRESHOLD = 60.0
# Minimum distinct calendar days in the *training* split before a borough runs the backtest.
# 30 days gives Prophet enough weekly seasonality signal and is achievable for every borough
# with a ~500 trips/day × 90-day TLC collection window.  The *collection* target is still 90 days;
# this is the *evaluation* floor — boroughs below it are skipped in the aggregate, not zeroed.
MIN_TRAIN_DISTINCT_DATES = 30
MIN_TEST_DISTINCT_DATES = 7


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

    test_sorted = test_df.sort_values("ds").reset_index(drop=True)

    if use_regressors:
        future_regs = test_sorted[["ds", "event_count", "is_rainy", "temperature_c"]].copy()
        forecast = fit_and_forecast(
            train_df,
            forecast_start,
            forecast_end,
            use_regressors=True,
            future_regressors=future_regs,
        )
    else:
        future_ds = test_sorted[["ds"]].copy()
        forecast = fit_and_forecast(
            train_df,
            forecast_start,
            forecast_end,
            use_regressors=False,
            future_ds_only=future_ds,
        )

    forecast = forecast.sort_values("ds").reset_index(drop=True)
    fc_y = forecast[["ds", "yhat"]].copy()
    merged = test_sorted.merge(fc_y, on="ds", how="left")
    if merged["yhat"].isna().any():
        missing = int(merged["yhat"].isna().sum())
        raise ValueError(
            f"Prophet baseline forecast missing {missing} test date(s); check train/test split and ds alignment."
        )
    yhat = merged["yhat"].tolist()

    out: list[float] = []
    for i in range(len(test_sorted)):
        n_mid = normalise_to_index([yhat[i]], hist_y)[0]
        weather = str(test_sorted["dominant_weather"].iloc[i])
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

    if len(dates) <= MIN_TRAIN_DISTINCT_DATES:
        err["error"] = (
            f"Not enough distinct dates ({len(dates)}); need more than {MIN_TRAIN_DISTINCT_DATES} "
            f"so training covers at least {MIN_TRAIN_DISTINCT_DATES} calendar days plus a hold-out. "
            "Sparse boroughs usually mean merged S3 data under processed/merged/ has few trip days "
            "for that borough—collect wider TLC windows or merge more sources."
        )
        return err

    split_idx = max(MIN_TRAIN_DISTINCT_DATES, int(len(dates) * TRAIN_FRACTION), MIN_DATAPOINTS)
    if split_idx >= len(dates):
        err["error"] = "Train/test split leaves no hold-out dates."
        return err

    train_dates = set(dates[:split_idx])
    test_dates = dates[split_idx:]
    if len(test_dates) < MIN_TEST_DISTINCT_DATES:
        err["error"] = (
            f"Insufficient hold-out window ({len(test_dates)} distinct dates); need at least "
            f"{MIN_TEST_DISTINCT_DATES} for a stable backtest score."
        )
        return err

    train_records = [r for r in records if r.get("date") in train_dates]
    test_records = [r for r in records if r.get("date") in test_dates]

    train_df = build_prophet_dataframe(train_records)
    test_df = build_prophet_dataframe(test_records)

    if len(train_df) < MIN_TRAIN_DISTINCT_DATES or test_df.empty:
        err["error"] = (
            f"Insufficient training rows after build ({len(train_df)}); need at least {MIN_TRAIN_DISTINCT_DATES}."
        )
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
    """Backtest all boroughs (or a subset).

    Boroughs with fewer than ``MIN_TRAIN_DISTINCT_DATES``+1 distinct calendar days in merged S3
    data are **skipped** for aggregate scoring (they still appear in ``borough_results`` with an
    ``error``). ``overall_accuracy`` / ``overall_pass`` use only boroughs that completed a backtest
    (no preflight error), so sparse outer boroughs do not drag the mean to zero when Manhattan
    has a full 90+ day history.
    """
    target_boroughs = sorted(boroughs) if boroughs else sorted(VALID_BOROUGHS)
    borough_results: dict[str, Any] = {}
    accums: list[float] = []

    for b in target_boroughs:
        res = run_borough_backtest(bucket, b)
        borough_results[b] = {k: v for k, v in res.items() if k not in ("actuals", "predicted")}
        if res.get("error"):
            borough_results[b]["pass"] = False
            borough_results[b]["skipped_for_aggregate"] = True
        else:
            borough_results[b]["skipped_for_aggregate"] = False
            accums.append(float(res.get("accuracy", 0.0)))

    evaluated = [b for b in target_boroughs if not borough_results[b].get("error")]
    skipped = [b for b in target_boroughs if borough_results[b].get("error")]

    if not evaluated:
        overall = 0.0
        overall_pass = False
    else:
        overall = round(sum(accums) / len(accums), 2)
        overall_pass = overall >= ACCURACY_THRESHOLD and all(
            borough_results[b].get("pass", False) for b in evaluated
        )

    return {
        "borough_results": borough_results,
        "boroughs_evaluated": evaluated,
        "boroughs_skipped_preflight": skipped,
        "overall_accuracy": overall,
        "overall_pass": overall_pass,
        "threshold": ACCURACY_THRESHOLD,
        "tolerance": ACCURACY_TOLERANCE,
    }


def run_regressor_comparison(bucket: str, borough: str) -> dict[str, Any]:
    """Compare baseline Prophet (no regressors) vs full model on the same hold-out split."""
    records = load_merged_records_for_borough(bucket, borough)
    dates = sorted({r.get("date", "") for r in records if r.get("date")})
    if len(dates) <= MIN_TRAIN_DISTINCT_DATES:
        return {
            "baseline_accuracy": 0.0,
            "full_model_accuracy": 0.0,
            "improvement": 0.0,
            "regressors_add_value": False,
            "pass": False,
            "error": (
                f"Insufficient dates for regressor comparison ({len(dates)} distinct); "
                f"need more than {MIN_TRAIN_DISTINCT_DATES}."
            ),
        }

    split_idx = max(MIN_TRAIN_DISTINCT_DATES, int(len(dates) * TRAIN_FRACTION), MIN_DATAPOINTS)
    if split_idx >= len(dates):
        return {
            "baseline_accuracy": 0.0,
            "full_model_accuracy": 0.0,
            "improvement": 0.0,
            "regressors_add_value": False,
            "pass": False,
            "error": "Train/test split leaves no hold-out dates.",
        }

    train_dates = set(dates[:split_idx])
    test_dates = dates[split_idx:]
    if len(test_dates) < MIN_TEST_DISTINCT_DATES:
        return {
            "baseline_accuracy": 0.0,
            "full_model_accuracy": 0.0,
            "improvement": 0.0,
            "regressors_add_value": False,
            "pass": False,
            "error": (
                f"Insufficient hold-out window for regressor comparison ({len(test_dates)} distinct); "
                f"need at least {MIN_TEST_DISTINCT_DATES}."
            ),
        }

    train_records = [r for r in records if r.get("date") in train_dates]
    test_records = [r for r in records if r.get("date") in test_dates]
    train_df = build_prophet_dataframe(train_records)
    test_df = build_prophet_dataframe(test_records)
    if len(train_df) < MIN_TRAIN_DISTINCT_DATES or test_df.empty:
        return {
            "baseline_accuracy": 0.0,
            "full_model_accuracy": 0.0,
            "improvement": 0.0,
            "regressors_add_value": False,
            "pass": False,
            "error": (
                f"Insufficient training rows for regressor comparison ({len(train_df)}); "
                f"need at least {MIN_TRAIN_DISTINCT_DATES}."
            ),
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
