"""
Integration smoke tests for the data-collection microservice.

These tests use REAL AWS S3. They are skipped by default and only run when
--run-integration is passed (wired to the 'main' branch job in CI).

What is mocked:    Third-party HTTP APIs (Open-Meteo, NYC TLC, Ticketmaster)
What is NOT mocked: AWS S3 — uses the real rushhour-data bucket

Each test writes to a unique key under integration-tests/ and deletes it
after, so the real bucket stays clean.

To run locally:
    AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_DEFAULT_REGION=... \\
    pytest tests/test_integration_data_collection.py --run-integration -v
"""

import json
import os
import sys
import uuid

import boto3
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "data-collection"))
os.environ.setdefault("TICKETMASTER_API_KEY", "test-key")

from collectWeather import (
    fetch_weather_data,
    transform_to_adage as weather_transform,
    save_to_s3,
    S3_BUCKET,
)
from collectNYCTaxi import (
    transform_to_adage as taxi_transform,
)
from collectTicketmaster import (
    transform_to_adage as tm_transform,
)


# ---------------------------------------------------------------------------
# Shared mock API payloads — identical shape to what the real APIs return
# ---------------------------------------------------------------------------

MOCK_WEATHER_RESPONSE = {
    "latitude": 40.7128,
    "longitude": -74.006,
    "timezone": "America/New_York",
    "hourly": {
        "time": ["2026-02-01T00:00", "2026-02-01T08:00"],
        "precipitation": [0.0, 3.5],
        "temperature_2m": [20.0, 14.0],
        "precipitation_probability": [0, 60],
    },
}

MOCK_TLC_RECORDS = [
    {
        "vendorid": "2",
        "tpep_pickup_datetime": "2026-03-14T08:15:00.000",
        "tpep_dropoff_datetime": "2026-03-14T08:38:30.000",
        "passenger_count": "1",
        "trip_distance": "4.8",
        "pulocationid": "161",
        "dolocationid": "230",
        "ratecodeid": "1",
        "payment_type": "1",
        "fare_amount": "18.50",
        "total_amount": "24.30",
        "congestion_surcharge": "2.50",
    }
]

MOCK_TM_RESPONSE = {
    "_embedded": {
        "events": [{
            "id": "INT-TEST-001",
            "name": "Integration Test Concert",
            "dates": {
                "start": {"localDate": "2026-04-15", "dateTime": "2026-04-15T19:00:00Z"},
                "end": {"dateTime": "2026-04-15T22:00:00Z"},
                "status": {"code": "onsale"},
            },
            "classifications": [{"segment": {"name": "Music"}, "genre": {"name": "Rock"}}],
            "_embedded": {
                "venues": [{
                    "name": "Test Venue NYC",
                    "city": {"name": "New York"},
                    "location": {"latitude": "40.7505", "longitude": "-73.9934"},
                }]
            },
        }]
    },
    "page": {"size": 1, "totalElements": 1, "totalPages": 1, "number": 0},
}


# ---------------------------------------------------------------------------
# Helper: unique S3 key per test so parallel runs never collide
# ---------------------------------------------------------------------------

def _test_key(service: str) -> str:
    run_id = os.environ.get("GITHUB_RUN_ID", str(uuid.uuid4())[:8])
    return f"integration-tests/{run_id}/{service}/smoke_test.json"


# ---------------------------------------------------------------------------
# Integration: S3 bucket accessibility
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_s3_bucket_is_accessible(real_aws_credentials, real_s3_bucket):
    """The rushhour-data S3 bucket exists and our credentials can reach it."""
    s3 = boto3.client("s3")
    response = s3.head_bucket(Bucket=real_s3_bucket)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


# ---------------------------------------------------------------------------
# Integration: Weather collector
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_weather_pipeline_writes_to_real_s3(real_aws_credentials, real_s3_bucket):
    """Weather fetch → transform → save writes valid ADAGE 3.0 JSON to real S3."""
    test_key = _test_key("weather")

    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_WEATHER_RESPONSE,
            raise_for_status=lambda: None,
        )
        raw = fetch_weather_data()

    adage = weather_transform(raw)
    save_to_s3(adage, real_s3_bucket, test_key)

    s3 = boto3.client("s3")
    try:
        stored = json.loads(s3.get_object(Bucket=real_s3_bucket, Key=test_key)["Body"].read())
        assert stored["data_source"] == "open_meteo"
        assert stored["dataset_type"] == "weather_forecast"
        assert len(stored["events"]) == 2
        assert stored["events"][0]["attribute"]["weather_category"] == "clear"
        assert stored["events"][1]["attribute"]["weather_category"] == "light_rain"
    finally:
        s3.delete_object(Bucket=real_s3_bucket, Key=test_key)


# ---------------------------------------------------------------------------
# Integration: NYC Taxi collector
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_taxi_pipeline_writes_to_real_s3(real_aws_credentials, real_s3_bucket):
    """Taxi transform → save writes valid ADAGE 3.0 JSON with zone enrichment to real S3."""
    test_key = _test_key("taxi")

    adage = taxi_transform(MOCK_TLC_RECORDS)
    save_to_s3(adage, real_s3_bucket, test_key)

    s3 = boto3.client("s3")
    try:
        stored = json.loads(s3.get_object(Bucket=real_s3_bucket, Key=test_key)["Body"].read())
        assert stored["data_source"] == "nyc_tlc"
        assert stored["dataset_type"] == "taxi_trips"
        assert len(stored["events"]) == 1
        assert stored["events"][0]["attribute"]["pickup_borough"] == "Manhattan"
        assert stored["events"][0]["attribute"]["pickup_zone"] == "Midtown Center"
    finally:
        s3.delete_object(Bucket=real_s3_bucket, Key=test_key)


# ---------------------------------------------------------------------------
# Integration: Ticketmaster collector
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_ticketmaster_pipeline_writes_to_real_s3(real_aws_credentials, real_s3_bucket):
    """Ticketmaster transform → save writes valid ADAGE 3.0 JSON to real S3."""
    test_key = _test_key("ticketmaster")

    adage = tm_transform(MOCK_TM_RESPONSE)
    save_to_s3(adage, real_s3_bucket, test_key)

    s3 = boto3.client("s3")
    try:
        stored = json.loads(s3.get_object(Bucket=real_s3_bucket, Key=test_key)["Body"].read())
        assert stored["data_source"] == "ticketmaster"
        assert stored["dataset_type"] == "public_events"
        assert len(stored["events"]) == 1
        assert stored["events"][0]["attribute"]["event_name"] == "Integration Test Concert"
        assert stored["events"][0]["event_type"] == "concert"
    finally:
        s3.delete_object(Bucket=real_s3_bucket, Key=test_key)