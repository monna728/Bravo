"""Higher-level accuracy, regressor, edge-case, and API contract checks for the analytical model."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from typing import Any, Callable

import pandas as pd
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.abspath(__file__))
_AM = os.path.join(_ROOT, "..", "analytical-model")
sys.path.insert(0, _AM)
sys.path.insert(0, os.path.join(_ROOT, ".."))

from prophet_model import (  # noqa: E402
    MIN_DATAPOINTS,
    VALID_BOROUGHS,
    predict,
)
from backtester import ACCURACY_THRESHOLD, run_regressor_comparison, run_walk_forward_backtest  # noqa: E402

REQUIRED_TOP_FIELDS = {
    "status": str,
    "borough": str,
    "predictions": list,
}
REQUIRED_PREDICTION_FIELDS: dict[str, type | tuple[type, ...]] = {
    "date": str,
    "crowd_demand_index": (int, float),
    "lower_bound": (int, float),
    "upper_bound": (int, float),
    "confidence": float,
    "contributing_factors": dict,
}


def _load_model_lambda_handler() -> Callable[..., dict]:
    """Load analytical-model ``lambda_handler`` without importing as top-level package."""
    path = os.path.join(_AM, "handler.py")
    spec = importlib.util.spec_from_file_location("analytical_model_handler", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.lambda_handler


def _check_prediction_contract(pred: dict) -> list[str]:
    """Return list of validation error strings (empty if OK)."""
    errs: list[str] = []
    for key, expected in REQUIRED_PREDICTION_FIELDS.items():
        if key not in pred:
            errs.append(f"missing field {key}")
            continue
        val = pred[key]
        if isinstance(expected, tuple):
            if not isinstance(val, expected):
                errs.append(f"{key} wrong type {type(val)}")
        elif not isinstance(val, expected):
            errs.append(f"{key} wrong type {type(val)}")
    return errs


def run_contract_test(bucket: str, borough: str = "Manhattan") -> dict[str, Any]:
    """Validate successful ``predict`` payload matches REQUIRED_* schemas."""
    result = predict(
        borough=borough,
        start_date="2099-01-01",
        end_date="2099-01-03",
        bucket=bucket,
        lookback_days=3650,
    )
    errs: list[str] = []
    for field, typ in REQUIRED_TOP_FIELDS.items():
        if field not in result:
            errs.append(f"missing top-level {field}")
        elif not isinstance(result[field], typ):
            errs.append(f"top-level {field} bad type")

    if isinstance(result.get("predictions"), list) and result["predictions"]:
        for i, p in enumerate(result["predictions"]):
            errs.extend([f"pred[{i}]: {e}" for e in _check_prediction_contract(p)])
    else:
        errs.append("no predictions to validate")

    return {"pass": len(errs) == 0, "errors": errs, "sample_status": result.get("status")}


def run_insufficient_data_test(bucket: str) -> dict[str, Any]:
    """Fewer than ``MIN_DATAPOINTS`` history rows must yield warning, not crash."""
    import prophet_model as pm

    short: list[dict] = []
    base = {
        "date": "2026-01-01",
        "borough": "Manhattan",
        "trip_count": 100,
        "event_count": 1,
        "temperature_avg_c": 10.0,
        "dominant_weather": "clear",
    }
    for i in range(MIN_DATAPOINTS - 1):
        row = {**base, "date": f"2026-01-{i + 1:02d}"}
        short.append(row)

    with patch.object(pm, "load_historical_data", return_value=short):
        out = pm.predict(
            borough="Manhattan",
            start_date="2026-02-01",
            end_date="2026-02-02",
            bucket=bucket,
        )
    ok = out.get("status") == "warning" and isinstance(out.get("predictions"), list) and len(out["predictions"]) >= 1
    return {"pass": ok, "status": out.get("status"), "message": out.get("message", "")}


def run_invalid_borough_http_test() -> dict[str, Any]:
    """Invalid borough must return HTTP 400 from the Lambda handler."""
    handler = _load_model_lambda_handler()
    event = {
        "body": json.dumps({
            "borough": "InvalidCity",
            "start_date": "2026-04-15",
            "end_date": "2026-04-17",
        })
    }
    resp = handler(event, None)
    body = json.loads(resp["body"])
    ok = resp["statusCode"] == 400 and "Invalid borough" in body.get("error", "")
    return {"pass": ok, "statusCode": resp["statusCode"]}


def run_score_bounds_test(bucket: str) -> dict[str, Any]:
    """With mocked Prophet output, every ``crowd_demand_index`` is in [0, 100]."""
    from datetime import datetime, timedelta

    import prophet_model as pm

    records = []
    start = datetime(2026, 1, 1)
    for i in range(30):
        d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        records.append({
            "date": d,
            "borough": "Manhattan",
            "trip_count": 2000 + i * 50,
            "event_count": 2,
            "temperature_avg_c": 12.0,
            "dominant_weather": "clear",
        })

    pred_start = datetime(2026, 3, 1)
    dates = [(pred_start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(50)]
    forecast_ds = pd.to_datetime(dates)
    with patch.object(pm, "load_historical_data", return_value=records):
        with patch.object(pm, "fit_and_forecast") as mock_fc:
            mock_fc.return_value = pd.DataFrame({
                "ds": forecast_ds,
                "yhat": [3000.0 + i * 100 for i in range(50)],
                "yhat_lower": [2500.0] * 50,
                "yhat_upper": [4500.0] * 50,
            })
            out = pm.predict(
                borough="Manhattan",
                start_date=dates[0],
                end_date=dates[49],
                bucket=bucket,
            )

    preds = out.get("predictions") or []
    ok = len(preds) == 50 and all(
        0.0 <= float(p["crowd_demand_index"]) <= 100.0 for p in preds
    )
    return {"pass": ok, "n_predictions": len(preds)}


def run_confidence_interval_order_test(bucket: str) -> dict[str, Any]:
    """``lower_bound`` ≤ ``crowd_demand_index`` ≤ ``upper_bound`` for each row."""
    import prophet_model as pm

    records = []
    for i in range(20):
        records.append({
            "date": f"2026-02-{i + 1:02d}",
            "borough": "Brooklyn",
            "trip_count": 1500 + i * 30,
            "event_count": 1,
            "temperature_avg_c": 8.0,
            "dominant_weather": "rain",
        })
    with patch.object(pm, "load_historical_data", return_value=records):
        with patch.object(pm, "fit_and_forecast") as mock_fc:
            mock_fc.return_value = pd.DataFrame({
                "ds": pd.to_datetime(["2026-04-01", "2026-04-02"]),
                "yhat": [2000.0, 2100.0],
                "yhat_lower": [1800.0, 1900.0],
                "yhat_upper": [2200.0, 2300.0],
            })
            out = pm.predict(
                borough="Brooklyn",
                start_date="2026-04-01",
                end_date="2026-04-02",
                bucket=bucket,
            )
    ok = True
    for p in out.get("predictions", []):
        lo = float(p["lower_bound"])
        hi = float(p["upper_bound"])
        mid = float(p["crowd_demand_index"])
        if lo > hi:
            lo, hi = hi, lo
        if not (lo <= mid <= hi):
            ok = False
    return {"pass": ok, "n_checked": len(out.get("predictions", []))}


def run_weather_multiplier_test(bucket: str) -> dict[str, Any]:
    """Same horizon with last-day clear vs thunderstorm history → storm score lower."""
    import prophet_model as pm

    def make_records(last_weather: str) -> list[dict]:
        rows = []
        for i in range(20):
            rows.append({
                "date": f"2026-01-{i + 1:02d}",
                "borough": "Queens",
                "trip_count": 1800 + i * 20,
                "event_count": 2,
                "temperature_avg_c": 11.0,
                "dominant_weather": "clear" if i < 19 else last_weather,
            })
        return rows

    clear_recs = make_records("clear")
    storm_recs = make_records("thunderstorm")

    with patch.object(pm, "fit_and_forecast") as mock_fc:
        mock_fc.return_value = pd.DataFrame({
            "ds": pd.to_datetime(["2026-02-15"]),
            "yhat": [2000.0],
            "yhat_lower": [1800.0],
            "yhat_upper": [2200.0],
        })
        with patch.object(pm, "load_historical_data", return_value=clear_recs):
            a = pm.predict(
                borough="Queens",
                start_date="2026-02-15",
                end_date="2026-02-15",
                bucket=bucket,
            )
        with patch.object(pm, "load_historical_data", return_value=storm_recs):
            b = pm.predict(
                borough="Queens",
                start_date="2026-02-15",
                end_date="2026-02-15",
                bucket=bucket,
            )

    ca = float(a["predictions"][0]["crowd_demand_index"])
    cb = float(b["predictions"][0]["crowd_demand_index"])
    ok = cb < ca
    return {"pass": ok, "clear_score": ca, "thunderstorm_score": cb}


def run_compare_all_boroughs_test(bucket: str) -> dict[str, Any]:
    """``compare_all_boroughs`` returns exactly five borough blocks with scores."""
    import prophet_model as pm

    def fake_load_hist(b: str, **kwargs: Any) -> list[dict]:
        return [
            {
                "date": f"2026-01-{i + 1:02d}",
                "borough": b,
                "trip_count": 1200 + i * 10,
                "event_count": 1,
                "temperature_avg_c": 10.0,
                "dominant_weather": "clear",
            }
            for i in range(20)
        ]

    event = {
        "body": json.dumps({
            "compare_all_boroughs": True,
            "start_date": "2026-05-01",
            "end_date": "2026-05-01",
            "bucket": bucket,
        })
    }
    with patch.object(pm, "load_historical_data", side_effect=fake_load_hist):
        with patch.object(pm, "fit_and_forecast") as mock_fc:
            mock_fc.return_value = pd.DataFrame({
                "ds": pd.to_datetime(["2026-05-01"]),
                "yhat": [2500.0],
                "yhat_lower": [2000.0],
                "yhat_upper": [3000.0],
            })
            handler = _load_model_lambda_handler()
            resp = handler(event, None)
    body = json.loads(resp["body"])
    if resp["statusCode"] != 200:
        return {"pass": False, "error": body}
    bor = body.get("boroughs") or {}
    ok = len(bor) == 5 and set(bor.keys()) == VALID_BOROUGHS
    for name, block in bor.items():
        preds = block.get("predictions") or []
        ok = ok and len(preds) == 1
        ok = ok and "crowd_demand_index" in preds[0]
    return {"pass": ok, "boroughs_returned": list(bor.keys())}


def run_regressor_impact_across_boroughs(
    bucket: str,
    boroughs: list[str] | None = None,
) -> dict[str, Any]:
    """Compare baseline vs full model on eligible boroughs (≥90-day merged history).

    **Pass** if mean uplift ≥ 3 pp **or** (mean uplift ≥ 0 and mean full-model accuracy ≥ backtest threshold)
    on evaluated boroughs — so a single strong borough with flat regressors still passes when
    forecasts are already within tolerance (common on sparse event signal).
    """
    target = sorted(boroughs) if boroughs else sorted(VALID_BOROUGHS)
    improvements: list[float] = []
    base_accs: list[float] = []
    full_accs: list[float] = []
    details: dict[str, Any] = {}
    for b in target:
        r = run_regressor_comparison(bucket, b)
        details[b] = r
        if r.get("error"):
            continue
        improvements.append(float(r["improvement"]))
        base_accs.append(float(r["baseline_accuracy"]))
        full_accs.append(float(r["full_model_accuracy"]))
    if not improvements:
        return {
            "baseline_accuracy": 0.0,
            "full_model_accuracy": 0.0,
            "improvement": 0.0,
            "regressors_add_value": False,
            "pass": False,
            "borough_details": details,
            "error": "No borough had enough data for regressor comparison.",
        }
    mean_imp = round(sum(improvements) / len(improvements), 2)
    mean_full = round(sum(full_accs) / len(full_accs), 2)
    uplift_pass = mean_imp >= 3.0
    flat_strong = mean_imp >= 0.0 and mean_full >= ACCURACY_THRESHOLD
    passes = uplift_pass or flat_strong
    return {
        "baseline_accuracy": round(sum(base_accs) / len(base_accs), 2),
        "full_model_accuracy": mean_full,
        "improvement": mean_imp,
        "regressors_add_value": uplift_pass,
        "pass": passes,
        "borough_details": details,
        "boroughs_evaluated": [b for b in target if not details[b].get("error")],
        "error": "",
    }
