import json
import pytest
import boto3
from moto import mock_aws
import importlib.util

import sys
import os

_retrieval_dir = os.path.join(os.path.dirname(__file__), "..", "services", "data-retrieval")
sys.path.insert(0, _retrieval_dir)

from s3_reader import (
    list_keys,
    read_json,
    get_prefix_for_source,
    filter_events_by_date,
    filter_events_by_type,
    filter_events_by_borough,
    retrieve,
    VALID_BOROUGHS,
)

_handler_spec = importlib.util.spec_from_file_location(
    "retrieval_handler", os.path.join(_retrieval_dir, "handler.py"))
_handler_mod = importlib.util.module_from_spec(_handler_spec)
_handler_spec.loader.exec_module(_handler_mod)
lambda_handler = _handler_mod.lambda_handler

BUCKET = "test-bucket"


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


MOCK_TICKETMASTER_ADAGE = {
    "data_source": "ticketmaster",
    "dataset_type": "public_events",
    "dataset_id": "s3://test-bucket/ticketmaster/raw/test.json",
    "time_object": {"timestamp": "2026-03-15 10:00:00.000000", "timezone": "America/New_York"},
    "events": [
        {
            "time_object": {"timestamp": "2026-04-15T19:00:00Z", "duration": 0, "duration_unit": "hour", "timezone": "America/New_York"},
            "event_type": "concert",
            "attribute": {"event_id": "e1", "event_name": "Rock Concert"},
        },
        {
            "time_object": {"timestamp": "2026-04-16T21:00:00Z", "duration": 0, "duration_unit": "hour", "timezone": "America/New_York"},
            "event_type": "sports",
            "attribute": {"event_id": "e2", "event_name": "Knicks Game"},
        },
        {
            "time_object": {"timestamp": "2026-04-20T20:00:00Z", "duration": 0, "duration_unit": "hour", "timezone": "America/New_York"},
            "event_type": "concert",
            "attribute": {"event_id": "e3", "event_name": "Jazz Night"},
        },
    ],
}

MOCK_WEATHER_ADAGE = {
    "data_source": "open_meteo",
    "dataset_type": "weather_forecast",
    "dataset_id": "s3://test-bucket/weather/raw/test.json",
    "time_object": {"timestamp": "2026-03-15 10:00:00.000000", "timezone": "America/New_York"},
    "events": [
        {
            "time_object": {"timestamp": "2026-04-15T08:00", "duration": 1, "duration_unit": "hour", "timezone": "America/New_York"},
            "event_type": "weather_forecast",
            "attribute": {"temperature_c": 15.0, "precipitation_mm": 0.0},
        },
    ],
}

MOCK_MERGED_ADAGE = {
    "data_source": "merged",
    "dataset_type": "demand_features",
    "dataset_id": "s3://test-bucket/processed/merged/test.json",
    "time_object": {"timestamp": "2026-03-15 10:00:00.000000", "timezone": "America/New_York"},
    "events": [
        {
            "time_object": {"timestamp": "2026-04-15 00:00:00.000000", "duration": 24, "duration_unit": "hour", "timezone": "America/New_York"},
            "event_type": "daily_demand_features",
            "attribute": {"date": "2026-04-15", "top_borough": "Manhattan", "trip_count": 5000, "event_count": 2, "temperature_avg_c": 15.0, "dominant_weather": "clear"},
        },
        {
            "time_object": {"timestamp": "2026-04-15 00:00:00.000000", "duration": 24, "duration_unit": "hour", "timezone": "America/New_York"},
            "event_type": "daily_demand_features",
            "attribute": {"date": "2026-04-15", "top_borough": "Brooklyn", "trip_count": 3200, "event_count": 1, "temperature_avg_c": 15.0, "dominant_weather": "clear"},
        },
        {
            "time_object": {"timestamp": "2026-04-16 00:00:00.000000", "duration": 24, "duration_unit": "hour", "timezone": "America/New_York"},
            "event_type": "daily_demand_features",
            "attribute": {"date": "2026-04-16", "top_borough": "Manhattan", "trip_count": 4800, "event_count": 1, "temperature_avg_c": 12.0, "dominant_weather": "rain"},
        },
    ],
}


def _setup_s3_with_data(s3):
    """Create bucket and upload test data."""
    s3.create_bucket(Bucket=BUCKET)
    s3.put_object(
        Bucket=BUCKET,
        Key="ticketmaster/raw/2026-04-15/events_NYC_20260415.json",
        Body=json.dumps(MOCK_TICKETMASTER_ADAGE),
        ContentType="application/json",
    )
    s3.put_object(
        Bucket=BUCKET,
        Key="weather/raw/2026-04-15/weather_40.7_-74.0_20260415.json",
        Body=json.dumps(MOCK_WEATHER_ADAGE),
        ContentType="application/json",
    )
    s3.put_object(
        Bucket=BUCKET,
        Key="processed/merged/merged_NYC_20260415.json",
        Body=json.dumps(MOCK_MERGED_ADAGE),
        ContentType="application/json",
    )


# ── get_prefix_for_source ───────────────────────────────────────────────────

def test_prefix_ticketmaster():
    assert get_prefix_for_source("ticketmaster") == "ticketmaster/raw"


def test_prefix_nyc_tlc():
    assert get_prefix_for_source("nyc_tlc") == "tlc/raw"


def test_prefix_weather():
    assert get_prefix_for_source("open_meteo") == "weather/raw"


def test_prefix_merged():
    assert get_prefix_for_source("merged") == "processed/merged"


def test_prefix_all_returns_none():
    assert get_prefix_for_source("all") is None


def test_prefix_unknown_raises():
    with pytest.raises(ValueError, match="Unknown source"):
        get_prefix_for_source("invalid_source")


# ── filter_events_by_date ───────────────────────────────────────────────────

def test_filter_by_date_no_filters():
    result = filter_events_by_date(MOCK_TICKETMASTER_ADAGE)
    assert len(result) == 3


def test_filter_by_start_date():
    result = filter_events_by_date(MOCK_TICKETMASTER_ADAGE, start_date="2026-04-16")
    assert len(result) == 2
    assert result[0]["attribute"]["event_id"] == "e2"


def test_filter_by_end_date():
    result = filter_events_by_date(MOCK_TICKETMASTER_ADAGE, end_date="2026-04-16")
    assert len(result) == 2
    assert result[0]["attribute"]["event_id"] == "e1"
    assert result[1]["attribute"]["event_id"] == "e2"


def test_filter_by_date_range():
    result = filter_events_by_date(MOCK_TICKETMASTER_ADAGE, start_date="2026-04-16", end_date="2026-04-16")
    assert len(result) == 1
    assert result[0]["attribute"]["event_name"] == "Knicks Game"


def test_filter_by_date_no_matches():
    result = filter_events_by_date(MOCK_TICKETMASTER_ADAGE, start_date="2026-05-01", end_date="2026-05-31")
    assert len(result) == 0


# ── filter_events_by_type ───────────────────────────────────────────────────

def test_filter_by_type_concert():
    events = MOCK_TICKETMASTER_ADAGE["events"]
    result = filter_events_by_type(events, "concert")
    assert len(result) == 2


def test_filter_by_type_sports():
    events = MOCK_TICKETMASTER_ADAGE["events"]
    result = filter_events_by_type(events, "sports")
    assert len(result) == 1
    assert result[0]["attribute"]["event_name"] == "Knicks Game"


def test_filter_by_type_no_match():
    events = MOCK_TICKETMASTER_ADAGE["events"]
    result = filter_events_by_type(events, "festival")
    assert len(result) == 0


# ── filter_events_by_borough ────────────────────────────────────────────────

def test_filter_by_borough_manhattan():
    events = MOCK_MERGED_ADAGE["events"]
    result = filter_events_by_borough(events, "Manhattan")
    assert len(result) == 2
    for e in result:
        assert e["attribute"]["top_borough"] == "Manhattan"


def test_filter_by_borough_brooklyn():
    events = MOCK_MERGED_ADAGE["events"]
    result = filter_events_by_borough(events, "Brooklyn")
    assert len(result) == 1
    assert result[0]["attribute"]["top_borough"] == "Brooklyn"


def test_filter_by_borough_no_match():
    events = MOCK_MERGED_ADAGE["events"]
    result = filter_events_by_borough(events, "Queens")
    assert len(result) == 0


def test_filter_by_borough_with_pickup_borough():
    events = [{"attribute": {"pickup_borough": "Bronx", "trip_distance": 3.0}}]
    result = filter_events_by_borough(events, "Bronx")
    assert len(result) == 1


def test_valid_boroughs_has_five():
    assert len(VALID_BOROUGHS) == 5
    assert "Manhattan" in VALID_BOROUGHS
    assert "Brooklyn" in VALID_BOROUGHS
    assert "Queens" in VALID_BOROUGHS
    assert "Bronx" in VALID_BOROUGHS
    assert "Staten Island" in VALID_BOROUGHS


# ── list_keys & read_json (S3 integration) ──────────────────────────────────

@mock_aws
def test_list_keys_returns_json_files(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    keys = list_keys(BUCKET, "ticketmaster/raw")
    assert len(keys) == 1
    assert keys[0].endswith(".json")


@mock_aws
def test_list_keys_empty_prefix(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    keys = list_keys(BUCKET, "nonexistent/prefix")
    assert keys == []


@mock_aws
def test_read_json_returns_dict(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    data = read_json(BUCKET, "ticketmaster/raw/2026-04-15/events_NYC_20260415.json")
    assert data["data_source"] == "ticketmaster"
    assert len(data["events"]) == 3


# ── retrieve (full flow) ────────────────────────────────────────────────────

@mock_aws
def test_retrieve_all_ticketmaster(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    result = retrieve(source="ticketmaster", bucket=BUCKET)
    assert result["status"] == "success"
    assert result["count"] == 3
    assert result["files_read"] == 1


@mock_aws
def test_retrieve_with_date_filter(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    result = retrieve(source="ticketmaster", bucket=BUCKET, start_date="2026-04-16")
    assert result["count"] == 2


@mock_aws
def test_retrieve_with_event_type_filter(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    result = retrieve(source="ticketmaster", bucket=BUCKET, event_type="concert")
    assert result["count"] == 2


@mock_aws
def test_retrieve_with_limit(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    result = retrieve(source="ticketmaster", bucket=BUCKET, limit=1)
    assert result["count"] == 1


@mock_aws
def test_retrieve_combined_filters(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    result = retrieve(
        source="ticketmaster", bucket=BUCKET,
        start_date="2026-04-15", end_date="2026-04-16", event_type="concert",
    )
    assert result["count"] == 1
    assert result["records"][0]["attribute"]["event_name"] == "Rock Concert"


@mock_aws
def test_retrieve_weather(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    result = retrieve(source="open_meteo", bucket=BUCKET)
    assert result["count"] == 1


@mock_aws
def test_retrieve_filters_in_response(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    result = retrieve(
        source="ticketmaster", bucket=BUCKET,
        start_date="2026-04-15", end_date="2026-04-20", event_type="concert", limit=5,
    )
    filters = result["filters_applied"]
    assert filters["start_date"] == "2026-04-15"
    assert filters["end_date"] == "2026-04-20"
    assert filters["event_type"] == "concert"
    assert filters["limit"] == 5


@mock_aws
def test_retrieve_merged_with_borough_manhattan(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    result = retrieve(source="merged", bucket=BUCKET, borough="Manhattan")
    assert result["status"] == "success"
    assert result["borough"] == "Manhattan"
    assert result["count"] == 2
    for rec in result["records"]:
        assert rec["attribute"]["top_borough"] == "Manhattan"


@mock_aws
def test_retrieve_merged_with_borough_brooklyn(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    result = retrieve(source="merged", bucket=BUCKET, borough="Brooklyn")
    assert result["borough"] == "Brooklyn"
    assert result["count"] == 1


@mock_aws
def test_retrieve_merged_no_borough_returns_all(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    result = retrieve(source="merged", bucket=BUCKET)
    assert result["borough"] == "all"
    assert result["count"] == 3


@mock_aws
def test_retrieve_merged_borough_no_match(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    result = retrieve(source="merged", bucket=BUCKET, borough="Queens")
    assert result["count"] == 0


@mock_aws
def test_retrieve_response_shape(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    result = retrieve(source="merged", bucket=BUCKET, borough="Manhattan")
    assert "status" in result
    assert "borough" in result
    assert "count" in result
    assert "records" in result
    assert "filters_applied" in result


# ── lambda_handler ──────────────────────────────────────────────────────────

@mock_aws
def test_handler_success(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    event = {"queryStringParameters": {"source": "ticketmaster", "bucket": BUCKET}}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "success"
    assert body["count"] == 3


@mock_aws
def test_handler_with_borough(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    event = {"queryStringParameters": {"source": "merged", "bucket": BUCKET, "borough": "Manhattan"}}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["borough"] == "Manhattan"
    assert body["count"] == 2


def test_handler_invalid_borough():
    event = {"queryStringParameters": {"source": "merged", "borough": "Hoboken"}}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid borough" in body["error"]
    assert "valid_boroughs" in body


def test_handler_invalid_source():
    response = lambda_handler({"queryStringParameters": {"source": "fake"}}, None)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Unknown source" in body["error"]
    assert "valid_sources" in body


def test_handler_invalid_limit():
    response = lambda_handler({"queryStringParameters": {"source": "ticketmaster", "limit": "abc"}}, None)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "limit must be an integer" in body["error"]


@mock_aws
def test_handler_processed_true_uses_merged(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    event = {"queryStringParameters": {"processed": "true", "bucket": BUCKET}}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["count"] == 3


@mock_aws
def test_handler_processed_with_borough(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    event = {"queryStringParameters": {"processed": "true", "bucket": BUCKET, "borough": "Brooklyn"}}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["borough"] == "Brooklyn"
    assert body["count"] == 1


@mock_aws
def test_handler_default_source_all(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    event = {"queryStringParameters": {"bucket": BUCKET}}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["count"] == 7  # 3 ticketmaster + 1 weather + 3 merged


@mock_aws
def test_handler_direct_invocation(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    _setup_s3_with_data(s3)

    event = {"source": "ticketmaster", "bucket": BUCKET}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["count"] == 3
