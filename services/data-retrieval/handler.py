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

sys.path.insert(0, os.path.dirname(__file__))

from s3_reader import retrieve, SOURCE_PREFIXES, VALID_BOROUGHS


def lambda_handler(event: dict, context) -> dict:
    """AWS Lambda entry point for data retrieval.

    Expects query parameters via event["queryStringParameters"] (API Gateway)
    or directly in the event dict (direct invocation).
    """
    params = event.get("queryStringParameters") or event
    source = params.get("source", "all")
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    event_type = params.get("event_type")
    borough = params.get("borough")
    limit = params.get("limit")
    processed = params.get("processed")
    bucket = params.get("bucket", os.environ.get("rushhour-data", "bucket-placeholder"))

    if borough and borough not in VALID_BOROUGHS:
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
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"status": "error", "error": str(e)}),
        }

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
