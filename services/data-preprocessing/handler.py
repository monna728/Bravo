"""Lambda handler for data preprocessing service.

Reads raw ADAGE data from S3, validates, normalises, merges by date,
and writes the merged output back to S3 in ADAGE 3.0 format.

Endpoint: POST /preprocess
"""

import json
import os
import boto3
import time
from datetime import datetime, timezone

import sys
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.adage_validator import validate_adage3
from shared.lambda_observability import deployment_env, emit_embedded_metric, log_event
from normaliser import normalise_ticketmaster, normalise_nyc_taxi, normalise_weather
from merger import merge_by_date, merged_to_adage

S3_BUCKET = os.environ.get("S3_BUCKET", "rushhour-data")
TIMEZONE = "America/New_York"

RAW_PREFIXES = {
    "ticketmaster": "ticketmaster/raw",
    "nyc_tlc": "tlc/raw",
    "open_meteo": "weather/raw",
}


def _read_s3_json(bucket: str, key: str) -> dict:
    """Read a JSON file from S3 and return as dict."""
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj["Body"].read().decode("utf-8"))


def _list_s3_keys(bucket: str, prefix: str) -> list[str]:
    """List all object keys under a given S3 prefix."""
    s3 = boto3.client("s3")
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".json"):
                keys.append(obj["Key"])
    return keys


def _save_to_s3(data: dict, bucket: str, key: str) -> None:
    """Save a dict as JSON to S3."""
    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data, indent=2),
        ContentType="application/json",
    )
    print(f"Saved to s3://{bucket}/{key}")


def _load_and_validate_source(bucket: str, prefix: str, source_name: str) -> list[dict]:
    """Load all JSON files under a prefix, validate each, return combined events."""
    keys = _list_s3_keys(bucket, prefix)
    all_data = []

    for key in keys:
        data = _read_s3_json(bucket, key)
        valid, msg = validate_adage3(data)
        if not valid:
            print(f"WARNING: {key} failed validation: {msg}")
            continue
        all_data.append(data)
        print(f"Loaded {key} ({len(data.get('events', []))} events)")

    return all_data


def preprocess(bucket: str = S3_BUCKET) -> dict:
    """Run the full preprocessing pipeline: load -> validate -> normalise -> merge."""
    tm_files = _load_and_validate_source(bucket, RAW_PREFIXES["ticketmaster"], "ticketmaster")
    taxi_files = _load_and_validate_source(bucket, RAW_PREFIXES["nyc_tlc"], "nyc_tlc")
    weather_files = _load_and_validate_source(bucket, RAW_PREFIXES["open_meteo"], "open_meteo")

    tm_daily = []
    for data in tm_files:
        tm_daily.extend(normalise_ticketmaster(data))

    taxi_daily = []
    for data in taxi_files:
        taxi_daily.extend(normalise_nyc_taxi(data))

    weather_daily = []
    for data in weather_files:
        weather_daily.extend(normalise_weather(data))

    merged = merge_by_date(tm_daily, taxi_daily, weather_daily)
    adage_output = merged_to_adage(merged, bucket=bucket)

    valid, msg = validate_adage3(adage_output)
    if not valid:
        print(f"ERROR: Merged output failed validation: {msg}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    s3_key = f"processed/merged/merged_NYC_{timestamp}.json"
    _save_to_s3(adage_output, bucket, s3_key)

    return {
        "merged_records": len(merged),
        "s3_key": s3_key,
        "sources": {
            "ticketmaster_files": len(tm_files),
            "taxi_files": len(taxi_files),
            "weather_files": len(weather_files),
        },
        "daily_records": {
            "ticketmaster": len(tm_daily),
            "taxi": len(taxi_daily),
            "weather": len(weather_daily),
        },
    }


def lambda_handler(event: dict, context) -> dict:
    """AWS Lambda entry point for preprocessing."""
    t0 = time.perf_counter()
    log_event("data-preprocessing", "preprocess started", context=context, event=event)

    bucket = event.get("bucket", S3_BUCKET)
    try:
        result = preprocess(bucket=bucket)
    except Exception as e:
        log_event(
            "data-preprocessing", "preprocess failed", level="ERROR", context=context, event=event,
            duration_ms=(time.perf_counter() - t0) * 1000, error_type=type(e).__name__,
        )
        raise

    elapsed_ms = (time.perf_counter() - t0) * 1000
    log_event(
        "data-preprocessing", "preprocess complete", context=context, event=event,
        duration_ms=elapsed_ms, merged_records=result["merged_records"], s3_key=result["s3_key"],
    )
    emit_embedded_metric(
        "Bravo",
        {"MergedRecordCount": float(result["merged_records"])},
        {"Service": "data-preprocessing", "Environment": deployment_env()},
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": "Preprocessing complete",
            **result,
        }),
    }


if __name__ == "__main__":
    print("Preprocessing handler — run via Lambda or import preprocess() directly.")
    print("For local testing, use test_preprocessing.py")
