import json
import pytest
import boto3
from moto import mock_aws
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "data-collection"))

os.environ["TICKETMASTER_API_KEY"] = "test-key"

from collectTicketmaster import (
    fetch_events,
    extract_venue_location,
    classify_event,
    extract_datetime,
    transform_to_adage,
    save_to_s3,
    S3_BUCKET,
)


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


MOCK_EVENT = {
    "id": "vvG1IZ9YJhpKAe",
    "name": "Madison Square Garden Concert",
    "url": "https://www.ticketmaster.com/event/vvG1IZ9YJhpKAe",
    "dates": {
        "start": {"localDate": "2026-04-15", "dateTime": "2026-04-15T19:00:00Z"},
        "end": {"dateTime": "2026-04-15T22:00:00Z"},
        "status": {"code": "onsale"},
    },
    "classifications": [
        {"segment": {"name": "Music"}, "genre": {"name": "Rock"}}
    ],
    "priceRanges": [{"min": 49.99, "max": 250.00, "currency": "USD"}],
    "_embedded": {
        "venues": [
            {
                "name": "Madison Square Garden",
                "city": {"name": "New York"},
                "location": {"latitude": "40.7505", "longitude": "-73.9934"},
            }
        ]
    },
}

MOCK_EVENT_MINIMAL = {
    "id": "abc123",
    "name": "Unknown Event",
    "dates": {"start": {"localDate": "2026-05-01"}, "status": {"code": "offsale"}},
}

MOCK_TM_RESPONSE = {
    "_embedded": {"events": [MOCK_EVENT, MOCK_EVENT_MINIMAL]},
    "page": {"size": 20, "totalElements": 2, "totalPages": 1, "number": 0},
}

MOCK_TM_EMPTY_RESPONSE = {
    "page": {"size": 20, "totalElements": 0, "totalPages": 0, "number": 0},
}


# ── extract_venue_location ───────────────────────────────────────────────────

def test_extract_venue_with_full_data():
    result = extract_venue_location(MOCK_EVENT)
    assert result["lat"] == 40.7505
    assert result["lng"] == -73.9934
    assert result["city"] == "New York"
    assert result["venue_name"] == "Madison Square Garden"


def test_extract_venue_with_no_venues():
    result = extract_venue_location(MOCK_EVENT_MINIMAL)
    assert result["lat"] is None
    assert result["lng"] is None
    assert result["city"] == ""
    assert result["venue_name"] == ""


# ── classify_event ───────────────────────────────────────────────────────────

def test_classify_music_event():
    assert classify_event(MOCK_EVENT) == "concert"


def test_classify_sports_event():
    sports_event = {"classifications": [{"segment": {"name": "Sports"}}]}
    assert classify_event(sports_event) == "sports"


def test_classify_unknown_segment():
    weird = {"classifications": [{"segment": {"name": "SomethingNew"}}]}
    assert classify_event(weird) == "other"


def test_classify_no_classifications():
    assert classify_event(MOCK_EVENT_MINIMAL) == "other"


# ── extract_datetime ─────────────────────────────────────────────────────────

def test_extract_datetime_full():
    start, end = extract_datetime(MOCK_EVENT)
    assert start == "2026-04-15T19:00:00Z"
    assert end == "2026-04-15T22:00:00Z"


def test_extract_datetime_local_date_only():
    start, end = extract_datetime(MOCK_EVENT_MINIMAL)
    assert start == "2026-05-01"
    assert end == ""


# ── transform_to_adage ──────────────────────────────────────────────────────

def test_transform_adage_structure():
    result = transform_to_adage(MOCK_TM_RESPONSE)
    assert result["data_source"] == "ticketmaster"
    assert result["dataset_type"] == "public_events"
    assert "time_object" in result
    assert "events" in result


def test_transform_adage_event_count():
    result = transform_to_adage(MOCK_TM_RESPONSE)
    assert len(result["events"]) == 2


def test_transform_adage_event_fields():
    result = transform_to_adage(MOCK_TM_RESPONSE)
    event = result["events"][0]
    assert event["event_type"] == "concert"
    attr = event["attribute"]
    assert attr["event_id"] == "vvG1IZ9YJhpKAe"
    assert attr["event_name"] == "Madison Square Garden Concert"
    assert attr["venue_name"] == "Madison Square Garden"
    assert attr["latitude"] == 40.7505
    assert attr["longitude"] == -73.9934
    assert attr["price_min"] == 49.99
    assert attr["price_max"] == 250.00
    assert attr["currency"] == "USD"
    assert attr["status"] == "onsale"


def test_transform_adage_minimal_event():
    result = transform_to_adage(MOCK_TM_RESPONSE)
    event = result["events"][1]
    attr = event["attribute"]
    assert attr["event_id"] == "abc123"
    assert attr["latitude"] is None
    assert attr["price_min"] is None
    assert attr["status"] == "offsale"


def test_transform_adage_empty_response():
    result = transform_to_adage(MOCK_TM_EMPTY_RESPONSE)
    assert result["events"] == []


def test_transform_adage_time_object():
    result = transform_to_adage(MOCK_TM_RESPONSE)
    event = result["events"][0]
    assert event["time_object"]["timestamp"] == "2026-04-15T19:00:00Z"
    assert event["time_object"]["duration"] == 0
    assert event["time_object"]["timezone"] == "America/New_York"


# ── fetch_events ─────────────────────────────────────────────────────────────

def test_fetch_events_calls_ticketmaster():
    with patch("collectTicketmaster.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_TM_RESPONSE,
            raise_for_status=lambda: None,
        )
        result = fetch_events(city="New York")

    mock_get.assert_called_once()
    call_args = mock_get.call_args
    assert "ticketmaster.com" in call_args[0][0]
    assert call_args[1]["params"]["city"] == "New York"
    assert call_args[1]["params"]["apikey"] == "test-key"


def test_fetch_events_passes_date_filters():
    with patch("collectTicketmaster.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_TM_RESPONSE,
            raise_for_status=lambda: None,
        )
        fetch_events(start_date="2026-04-01", end_date="2026-04-30")

    params = mock_get.call_args[1]["params"]
    assert params["startDateTime"] == "2026-04-01T00:00:00Z"
    assert params["endDateTime"] == "2026-04-30T23:59:59Z"


def test_fetch_events_passes_classification():
    with patch("collectTicketmaster.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_TM_RESPONSE,
            raise_for_status=lambda: None,
        )
        fetch_events(classification="Music")

    params = mock_get.call_args[1]["params"]
    assert params["classificationName"] == "Music"


def test_fetch_events_raises_without_api_key():
    with patch("collectTicketmaster.API_KEY", ""):
        with pytest.raises(ValueError, match="TICKETMASTER_API_KEY"):
            fetch_events()


# ── save_to_s3 ───────────────────────────────────────────────────────────────

@mock_aws
def test_save_to_s3_writes_correct_data(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="bucket-placeholder")

    save_to_s3({"test_key": "test_value"}, "bucket-placeholder", "ticketmaster/raw/test.json")

    obj = s3.get_object(Bucket="bucket-placeholder", Key="ticketmaster/raw/test.json")
    body = json.loads(obj["Body"].read())
    assert body["test_key"] == "test_value"


@mock_aws
def test_save_to_s3_stores_valid_adage(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="bucket-placeholder")

    adage_data = transform_to_adage(MOCK_TM_RESPONSE)
    save_to_s3(adage_data, "bucket-placeholder", "ticketmaster/raw/adage_test.json")

    obj = s3.get_object(Bucket="bucket-placeholder", Key="ticketmaster/raw/adage_test.json")
    stored = json.loads(obj["Body"].read())
    assert stored["data_source"] == "ticketmaster"
    assert len(stored["events"]) == 2


# ── full pipeline ────────────────────────────────────────────────────────────

@mock_aws
def test_full_pipeline_fetch_transform_save(aws_credentials):
    """End-to-end: mock API call -> transform -> write to S3 -> verify."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="bucket-placeholder")

    with patch("collectTicketmaster.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_TM_RESPONSE,
            raise_for_status=lambda: None,
        )
        raw = fetch_events()

    adage_data = transform_to_adage(raw)
    save_to_s3(adage_data, "bucket-placeholder", "ticketmaster/raw/integration_test.json")

    obj = s3.get_object(Bucket="bucket-placeholder", Key="ticketmaster/raw/integration_test.json")
    stored = json.loads(obj["Body"].read())

    assert stored["data_source"] == "ticketmaster"
    assert len(stored["events"]) == 2
    assert stored["events"][0]["attribute"]["event_name"] == "Madison Square Garden Concert"
    assert stored["events"][0]["event_type"] == "concert"