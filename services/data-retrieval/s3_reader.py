"""Read and filter ADAGE 3.0 data stored in S3.

Provides functions to list, load, and filter JSON files from S3 by source,
date range, event type, and borough. This is the core logic behind the
GET /retrieve endpoint — it never writes, only reads.
"""

import json
import os
import boto3
from datetime import datetime

S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "bucket-placeholder")

VALID_BOROUGHS = {"Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"}

SOURCE_PREFIXES = {
    "ticketmaster": "ticketmaster/raw",
    "nyc_tlc": "tlc/raw",
    "open_meteo": "weather/raw",
    "merged": "processed/merged",
}


def list_keys(bucket: str, prefix: str) -> list[str]:
    """List all .json object keys under a given S3 prefix."""
    s3 = boto3.client("s3")
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".json"):
                keys.append(obj["Key"])
    return keys


def read_json(bucket: str, key: str) -> dict:
    """Read a single JSON file from S3 and return as a dict."""
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj["Body"].read().decode("utf-8"))


def get_prefix_for_source(source: str) -> str:
    """Map a source name to its S3 prefix. Raises ValueError if unknown."""
    if source == "all":
        return None
    prefix = SOURCE_PREFIXES.get(source)
    if prefix is None:
        valid = ", ".join(list(SOURCE_PREFIXES.keys()) + ["all"])
        raise ValueError(f"Unknown source '{source}'. Valid sources: {valid}")
    return prefix


def filter_events_by_date(
    adage_data: dict,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """Filter events from an ADAGE dict to only those within a date range."""
    events = adage_data.get("events", [])
    if not start_date and not end_date:
        return events

    filtered = []
    for event in events:
        ts = event.get("time_object", {}).get("timestamp", "")
        event_date = _extract_date(ts)
        if not event_date:
            continue
        if start_date and event_date < start_date:
            continue
        if end_date and event_date > end_date:
            continue
        filtered.append(event)
    return filtered


def filter_events_by_type(events: list[dict], event_type: str) -> list[dict]:
    """Filter a list of events to only those matching a given event_type."""
    return [e for e in events if e.get("event_type") == event_type]


def filter_events_by_borough(events: list[dict], borough: str) -> list[dict]:
    """Filter events to only those matching a given borough.

    Checks attribute.top_borough (merged data), attribute.pickup_borough
    (taxi data), or attribute.city (ticketmaster/weather) for a match.
    """
    filtered = []
    for event in events:
        attr = event.get("attribute", {})
        event_borough = (
            attr.get("top_borough")
            or attr.get("pickup_borough")
            or attr.get("borough")
            or ""
        )
        if event_borough == borough:
            filtered.append(event)
    return filtered


def retrieve(
    source: str,
    bucket: str = S3_BUCKET,
    start_date: str | None = None,
    end_date: str | None = None,
    event_type: str | None = None,
    borough: str | None = None,
    limit: int | None = None,
) -> dict:
    """Retrieve and filter data from S3 for a given source.

    Returns a response with status, borough, count, and records.
    """
    if source == "all":
        prefixes = list(SOURCE_PREFIXES.values())
    else:
        prefixes = [get_prefix_for_source(source)]

    all_events = []
    files_read = 0

    for prefix in prefixes:
        keys = list_keys(bucket, prefix)
        for key in keys:
            data = read_json(bucket, key)
            events = filter_events_by_date(data, start_date, end_date)
            if event_type:
                events = filter_events_by_type(events, event_type)
            if borough:
                events = filter_events_by_borough(events, borough)
            all_events.extend(events)
            files_read += 1

    if limit and len(all_events) > limit:
        all_events = all_events[:limit]

    return {
        "status": "success",
        "borough": borough or "all",
        "count": len(all_events),
        "files_read": files_read,
        "filters_applied": {
            "source": source,
            "start_date": start_date,
            "end_date": end_date,
            "event_type": event_type,
            "borough": borough,
            "limit": limit,
        },
        "records": all_events,
    }


def _extract_date(timestamp: str) -> str:
    """Extract YYYY-MM-DD from various timestamp formats."""
    if not timestamp:
        return ""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M",
                "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
        try:
            return datetime.strptime(timestamp, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return timestamp[:10] if len(timestamp) >= 10 else ""
