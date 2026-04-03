import json
import os
import sys
import time
import boto3
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.lambda_observability import deployment_env, emit_embedded_metric, log_event

TICKETMASTER_API = "https://app.ticketmaster.com/discovery/v2/events.json"
API_KEY = os.environ.get("TICKETMASTER_API_KEY", "")
S3_BUCKET = "S3_BUCKET"
S3_KEY_PREFIX = "ticketmaster/raw"
DEFAULT_CITY = "New York"
DEFAULT_STATE = "NY"
DEFAULT_COUNTRY = "US"
DEFAULT_SIZE = 50
TIMEZONE = "America/New_York"

CLASSIFICATION_MAP = {
    "Music": "concert",
    "Sports": "sports",
    "Arts & Theatre": "arts_theatre",
    "Film": "film",
    "Miscellaneous": "miscellaneous",
}


def fetch_events(
    city: str = DEFAULT_CITY,
    state_code: str = DEFAULT_STATE,
    country_code: str = DEFAULT_COUNTRY,
    start_date: str | None = None,
    end_date: str | None = None,
    classification: str | None = None,
    size: int = DEFAULT_SIZE,
    page: int = 0,
) -> dict:
    """Fetch events from the Ticketmaster Discovery API."""
    if not API_KEY:
        raise ValueError("TICKETMASTER_API_KEY environment variable is not set")

    params: dict = {
        "apikey": API_KEY,
        "city": city,
        "stateCode": state_code,
        "countryCode": country_code,
        "size": size,
        "page": page,
    }

    if start_date:
        params["startDateTime"] = f"{start_date}T00:00:00Z"
    if end_date:
        params["endDateTime"] = f"{end_date}T23:59:59Z"
    if classification:
        params["classificationName"] = classification

    response = requests.get(TICKETMASTER_API, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def extract_venue_location(event_raw: dict) -> dict:
    """Pull lat/lng/city/venue from the nested _embedded.venues structure."""
    venues = event_raw.get("_embedded", {}).get("venues", [])
    if not venues:
        return {"lat": None, "lng": None, "city": "", "venue_name": ""}

    venue = venues[0]
    location = venue.get("location", {})
    city_obj = venue.get("city", {})
    return {
        "lat": float(location["latitude"]) if "latitude" in location else None,
        "lng": float(location["longitude"]) if "longitude" in location else None,
        "city": city_obj.get("name", ""),
        "venue_name": venue.get("name", ""),
    }


def classify_event(event_raw: dict) -> str:
    """Map Ticketmaster classification segment to our event type."""
    classifications = event_raw.get("classifications", [])
    if not classifications:
        return "other"
    segment_name = classifications[0].get("segment", {}).get("name", "")
    return CLASSIFICATION_MAP.get(segment_name, "other")


def extract_datetime(event_raw: dict) -> tuple[str, str]:
    """Extract start and end datetimes in ISO 8601 format."""
    dates = event_raw.get("dates", {})
    start = dates.get("start", {})
    end = dates.get("end", {})

    start_dt = start.get("dateTime", start.get("localDate", ""))
    end_dt = end.get("dateTime", end.get("localDate", ""))
    return start_dt, end_dt


def transform_to_adage(raw_response: dict, city: str = DEFAULT_CITY) -> dict:
    """Convert raw Ticketmaster response into ADAGE 3.0 data model format."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    s3_key = f"{S3_KEY_PREFIX}/{date_str}/events_{city}_{now.replace(' ', '_')}.json"

    adage_output = {
        "data_source": "ticketmaster",
        "dataset_type": "public_events",
        "dataset_id": f"s3://{S3_BUCKET}/{s3_key}",
        "time_object": {
            "timestamp": now,
            "timezone": TIMEZONE,
        },
        "events": [],
    }

    raw_events = raw_response.get("_embedded", {}).get("events", [])

    for raw_event in raw_events:
        venue_info = extract_venue_location(raw_event)
        event_type = classify_event(raw_event)
        start_dt, end_dt = extract_datetime(raw_event)

        event = {
            "time_object": {
                "timestamp": start_dt,
                "duration": 0,
                "duration_unit": "hour",
                "timezone": TIMEZONE,
            },
            "event_type": event_type,
            "attribute": {
                "event_id": raw_event.get("id", ""),
                "event_name": raw_event.get("name", ""),
                "event_url": raw_event.get("url", ""),
                "start_datetime": start_dt,
                "end_datetime": end_dt,
                "venue_name": venue_info["venue_name"],
                "city": venue_info["city"],
                "latitude": venue_info["lat"],
                "longitude": venue_info["lng"],
                "classification": event_type,
                "price_min": None,
                "price_max": None,
                "currency": None,
                "status": raw_event.get("dates", {}).get("status", {}).get("code", ""),
            },
        }

        price_ranges = raw_event.get("priceRanges", [])
        if price_ranges:
            event["attribute"]["price_min"] = price_ranges[0].get("min")
            event["attribute"]["price_max"] = price_ranges[0].get("max")
            event["attribute"]["currency"] = price_ranges[0].get("currency")

        adage_output["events"].append(event)

    return adage_output


def save_to_s3(data: dict, bucket: str, key: str) -> None:
    """Save a Python dict as a JSON file to S3."""
    s3_client = boto3.client("s3")
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data, indent=2),
        ContentType="application/json",
    )
    print(f"Saved to s3://{bucket}/{key}")


def lambda_handler(event: dict, context) -> dict:
    """AWS Lambda entry point for Ticketmaster data collection."""
    t0 = time.perf_counter()
    log_event("collect-ticketmaster", "collection started", context=context, event=event or {})
    city = event.get("city", DEFAULT_CITY)
    state_code = event.get("state_code", DEFAULT_STATE)
    country_code = event.get("country_code", DEFAULT_COUNTRY)
    start_date = event.get("start_date")
    end_date = event.get("end_date")
    classification = event.get("classification")

    try:
        raw_response = fetch_events(
            city=city,
            state_code=state_code,
            country_code=country_code,
            start_date=start_date,
            end_date=end_date,
            classification=classification,
        )

        total = raw_response.get("page", {}).get("totalElements", 0)
        print(f"Fetched page with {total} total events from Ticketmaster for {city}")

        adage_data = transform_to_adage(raw_response, city=city)
        print(f"Transformed {len(adage_data['events'])} events into ADAGE format")

        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        s3_key = f"{S3_KEY_PREFIX}/{date_str}/events_{city}_{timestamp}.json"

        save_to_s3(adage_data, S3_BUCKET, s3_key)
    except Exception as e:
        log_event(
            "collect-ticketmaster", "collection failed", level="ERROR", context=context, event=event or {},
            duration_ms=(time.perf_counter() - t0) * 1000, error_type=type(e).__name__,
        )
        raise

    n = len(adage_data["events"])
    elapsed_ms = (time.perf_counter() - t0) * 1000
    log_event(
        "collect-ticketmaster", "collection complete", context=context, event=event or {},
        duration_ms=elapsed_ms, records_collected=n, s3_key=s3_key, city=city,
    )
    emit_embedded_metric(
        "Bravo",
        {"RecordsCollected": float(n)},
        {"Service": "collect-ticketmaster", "Environment": deployment_env()},
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": "Ticketmaster data collection complete",
            "records_collected": n,
            "total_available": total,
            "s3_location": f"s3://{S3_BUCKET}/{s3_key}",
        }),
    }

if __name__ == "__main__":
    print("Running local test (simulating Lambda)...")

    response = lambda_handler(event={}, context=None)

    print("Lambda response:")
    print(json.dumps(response, indent=2))
