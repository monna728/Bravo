"""Lambda handler for data retrieval service.

Reads stored ADAGE data from S3 based on query parameters and returns
filtered results as JSON. Supports filtering by source, date range,
event type, borough, and limit.

Endpoint: GET /retrieve
Query params: source, start_date, end_date, event_type, borough, limit, processed
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.lambda_observability import deployment_env, emit_embedded_metric, log_event
from s3_reader import retrieve, SOURCE_PREFIXES, VALID_BOROUGHS

_SERVICE = "data-retrieval"


def lambda_handler(event: dict, context) -> dict:
    """AWS Lambda entry point for data retrieval.

    Expects query parameters via event["queryStringParameters"] (API Gateway)
    or directly in the event dict (direct invocation).
    """
    t0 = time.perf_counter()
    params = event.get("queryStringParameters") or event
    source = params.get("source", "all")
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    event_type = params.get("event_type")
    borough = params.get("borough")
    limit = params.get("limit")
    processed = params.get("processed")
    bucket = params.get("bucket", os.environ.get("S3_BUCKET", "bucket-placeholder"))

    if borough and borough not in VALID_BOROUGHS:
        log_event(
            _SERVICE, "validation failed: invalid borough", level="ERROR", context=context, event=event,
            duration_ms=(time.perf_counter() - t0) * 1000, borough=borough,
        )
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "error",
                "error": f"Invalid borough: {borough}",
                "valid_boroughs": sorted(list(VALID_BOROUGHS)),
            }),
        }

    if source not in SOURCE_PREFIXES and source != "all":
        log_event(
            _SERVICE, "validation failed: unknown source", level="ERROR", context=context, event=event,
            duration_ms=(time.perf_counter() - t0) * 1000, source=source,
        )
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "error",
                "error": f"Unknown source: {source}",
                "valid_sources": list(SOURCE_PREFIXES.keys()) + ["all"],
            }),
        }

    if limit:
        try:
            limit = int(limit)
        except ValueError:
            log_event(
                _SERVICE, "validation failed: limit not integer", level="ERROR", context=context, event=event,
                duration_ms=(time.perf_counter() - t0) * 1000,
            )
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"status": "error", "error": "limit must be an integer"}),
            }

    if processed and processed.lower() == "true":
        source = "merged"

    try:
        result = retrieve(
            source=source,
            bucket=bucket,
            start_date=start_date,
            end_date=end_date,
            event_type=event_type,
            borough=borough,
            limit=limit,
        )
    except Exception as e:
        log_event(
            _SERVICE, "retrieve failed", level="ERROR", context=context, event=event,
            duration_ms=(time.perf_counter() - t0) * 1000, error_type=type(e).__name__,
        )
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"status": "error", "error": str(e)}),
        }

    elapsed_ms = (time.perf_counter() - t0) * 1000
    log_event(
        _SERVICE, "retrieve ok", context=context, event=event, duration_ms=elapsed_ms,
        source=source, borough=borough or "all", record_count=result.get("count", 0),
    )
    emit_embedded_metric(
        "Bravo",
        {"RecordsRetrieved": float(result.get("count", 0))},
        {"Service": "data-retrieval", "Environment": deployment_env()},
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(result),
    }


if __name__ == "__main__":
    print("Data Retrieval Service")
    print(f"Available sources: {list(SOURCE_PREFIXES.keys()) + ['all']}")
    print(f"Valid boroughs: {sorted(list(VALID_BOROUGHS))}")
    print("Example: GET /retrieve?source=merged&borough=Manhattan&start_date=2024-01-01&end_date=2024-01-31")
