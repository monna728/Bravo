"""Lambda handler for the analytical model service.

Exposes POST /predict — accepts a borough, date range, and optional filters,
then returns a Crowd Demand Index prediction (0–100) powered by Prophet.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.cors import CORS_HEADERS
from shared.lambda_observability import deployment_env, emit_embedded_metric, log_event
from prophet_model import predict, VALID_BOROUGHS, TIME_OF_DAY_FACTORS


VALID_TIME_OF_DAY = set(TIME_OF_DAY_FACTORS.keys())
_SERVICE = "analytical-model"


def lambda_handler(event: dict, context) -> dict:
    """AWS Lambda entry point for POST /predict.

    Expects a JSON body with:
        borough (required): one of Manhattan, Brooklyn, Queens, Bronx, Staten Island
        start_date (required): YYYY-MM-DD
        end_date (required): YYYY-MM-DD
        time_of_day (optional): morning, afternoon, evening, night, all (default: all)
        event_type (optional): filter by event type
        compare_all_boroughs (optional): if true, returns predictions for all 5 boroughs
    """
    t0 = time.perf_counter()

    def _fail(status: int, msg: str) -> dict:
        log_event(
            _SERVICE, "request validation failed", level="ERROR", context=context, event=event,
            duration_ms=(time.perf_counter() - t0) * 1000, http_status=status,
        )
        return _error_response(status, msg)

    try:
        body = _parse_body(event)
    except ValueError as e:
        return _fail(400, str(e))

    borough = body.get("borough")
    start_date = body.get("start_date")
    end_date = body.get("end_date")
    time_of_day = body.get("time_of_day", "all")
    event_type = body.get("event_type")
    compare_all = body.get("compare_all_boroughs", False)
    bucket = body.get("bucket", os.environ.get("S3_BUCKET", "bucket-placeholder"))

    if not compare_all and not borough:
        return _fail(400, "borough is required (or set compare_all_boroughs to true)")

    if not start_date:
        return _fail(400, "start_date is required (YYYY-MM-DD)")

    if not end_date:
        return _fail(400, "end_date is required (YYYY-MM-DD)")

    if borough and borough not in VALID_BOROUGHS:
        return _fail(400, f"Invalid borough: {borough}. Valid: {sorted(VALID_BOROUGHS)}")

    if time_of_day not in VALID_TIME_OF_DAY:
        return _fail(400, f"Invalid time_of_day: {time_of_day}. Valid: {sorted(VALID_TIME_OF_DAY)}")

    if not _is_valid_date(start_date):
        return _fail(400, f"Invalid start_date format: {start_date}. Use YYYY-MM-DD")

    if not _is_valid_date(end_date):
        return _fail(400, f"Invalid end_date format: {end_date}. Use YYYY-MM-DD")

    if start_date > end_date:
        return _fail(400, "start_date must be before or equal to end_date")

    try:
        if compare_all:
            result = _predict_all_boroughs(start_date, end_date, time_of_day, event_type, bucket)
        else:
            result = predict(
                borough=borough,
                start_date=start_date,
                end_date=end_date,
                time_of_day=time_of_day,
                event_type=event_type,
                bucket=bucket,
            )
    except Exception as e:
        log_event(
            _SERVICE, "predict failed", level="ERROR", context=context, event=event,
            duration_ms=(time.perf_counter() - t0) * 1000, error_type=type(e).__name__,
        )
        return _error_response(500, f"Prediction failed: {str(e)}")

    pred_count = _prediction_row_count(result, compare_all)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    log_event(
        _SERVICE, "predict ok", context=context, event=event, duration_ms=elapsed_ms,
        borough=borough or "all", compare_all_boroughs=compare_all, prediction_rows=pred_count,
        model_status=result.get("status") if isinstance(result, dict) else None,
    )
    emit_embedded_metric(
        "Bravo",
        {"PredictionsGenerated": float(pred_count)},
        {
            "Service": "analytical-model",
            "Environment": deployment_env(),
            "Borough": borough or ("compare_all" if compare_all else "unknown"),
        },
    )

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": json.dumps(result),
    }


def _prediction_row_count(result: dict, compare_all: bool) -> int:
    """Approximate number of prediction rows returned (for metrics)."""
    if compare_all and isinstance(result.get("boroughs"), dict):
        total = 0
        for block in result["boroughs"].values():
            if isinstance(block, dict):
                total += len(block.get("predictions") or [])
        return total
    if isinstance(result.get("predictions"), list):
        return len(result["predictions"])
    return 0


def _predict_all_boroughs(
    start_date: str,
    end_date: str,
    time_of_day: str,
    event_type: str | None,
    bucket: str,
) -> dict:
    """Run predictions for all 5 boroughs and return side-by-side results."""
    borough_results = {}
    for b in sorted(VALID_BOROUGHS):
        borough_results[b] = predict(
            borough=b,
            start_date=start_date,
            end_date=end_date,
            time_of_day=time_of_day,
            event_type=event_type,
            bucket=bucket,
        )

    return {
        "status": "success",
        "compare_all_boroughs": True,
        "boroughs": borough_results,
    }


def _parse_body(event: dict) -> dict:
    """Extract the request body from a Lambda event (API Gateway or direct)."""
    if "body" in event and event["body"]:
        body = event["body"]
        if isinstance(body, str):
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in request body")
        return body
    return event


def _is_valid_date(date_str: str) -> bool:
    """Check if a string is in YYYY-MM-DD format."""
    if not date_str or len(date_str) != 10:
        return False
    try:
        from datetime import datetime
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _error_response(status_code: int, message: str) -> dict:
    """Build a standard error response."""
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps({"status": "error", "error": message}),
    }


if __name__ == "__main__":
    print("Analytical Model Service — POST /predict")
    print(f"Valid boroughs: {sorted(VALID_BOROUGHS)}")
    print(f"Valid time_of_day: {sorted(VALID_TIME_OF_DAY)}")
    print("Example request body:")
    print(json.dumps({
        "borough": "Manhattan",
        "start_date": "2026-04-15",
        "end_date": "2026-04-17",
        "time_of_day": "evening",
        "compare_all_boroughs": False,
    }, indent=2))
