import json
import pytest
import boto3
from moto import mock_aws
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "data-collection"))

from collectNYCTaxi import (
    fetch_tlc_data,
    calculate_duration_minutes,
    transform_to_adage,
    save_to_s3,
    S3_BUCKET,
)


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


MOCK_TLC_RECORD_1 = {
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

MOCK_TLC_RECORD_2 = {
    "vendorid": "1",
    "tpep_pickup_datetime": "2026-03-14T12:00:00.000",
    "tpep_dropoff_datetime": "2026-03-14T12:10:00.000",
    "passenger_count": "3",
    "trip_distance": "1.2",
    "pulocationid": "237",
    "dolocationid": "140",
    "ratecodeid": "1",
    "payment_type": "2",
    "fare_amount": "8.00",
    "total_amount": "11.80",
    "congestion_surcharge": "0.00",
}

MOCK_TLC_RECORDS = [MOCK_TLC_RECORD_1, MOCK_TLC_RECORD_2]


# ── calculate_duration_minutes ───────────────────────────────────────────────

def test_duration_normal_trip():
    result = calculate_duration_minutes(
        "2026-03-14T08:15:00.000", "2026-03-14T08:38:30.000"
    )
    assert result == 23.5


def test_duration_short_trip():
    result = calculate_duration_minutes(
        "2026-03-14T12:00:00.000", "2026-03-14T12:10:00.000"
    )
    assert result == 10.0


def test_duration_zero_trip():
    result = calculate_duration_minutes(
        "2026-03-14T08:00:00.000", "2026-03-14T08:00:00.000"
    )
    assert result == 0


def test_duration_invalid_format():
    result = calculate_duration_minutes("bad-date", "also-bad")
    assert result == 0


def test_duration_empty_strings():
    result = calculate_duration_minutes("", "")
    assert result == 0


# ── transform_to_adage ──────────────────────────────────────────────────────

def test_transform_adage_structure():
    result = transform_to_adage(MOCK_TLC_RECORDS)
    assert result["data_source"] == "nyc_tlc"
    assert result["dataset_type"] == "taxi_trips"
    assert "time_object" in result
    assert "events" in result


def test_transform_adage_event_count():
    result = transform_to_adage(MOCK_TLC_RECORDS)
    assert len(result["events"]) == 2


def test_transform_adage_event_type():
    result = transform_to_adage(MOCK_TLC_RECORDS)
    for event in result["events"]:
        assert event["event_type"] == "taxi_pickup"


def test_transform_adage_first_event_attributes():
    result = transform_to_adage(MOCK_TLC_RECORDS)
    attr = result["events"][0]["attribute"]
    assert attr["vendorid"] == 2
    assert attr["pulocationid"] == 161
    assert attr["dolocationid"] == 230
    assert attr["passenger_count"] == 1.0
    assert attr["trip_distance"] == 4.8
    assert attr["fare_amount"] == 18.50
    assert attr["total_amount"] == 24.30
    assert attr["payment_type"] == 1
    assert attr["congestion_surcharge"] == 2.50
    assert attr["ratecodeid"] == 1.0


def test_transform_adage_second_event_attributes():
    result = transform_to_adage(MOCK_TLC_RECORDS)
    attr = result["events"][1]["attribute"]
    assert attr["vendorid"] == 1
    assert attr["pulocationid"] == 237
    assert attr["dolocationid"] == 140
    assert attr["passenger_count"] == 3.0
    assert attr["trip_distance"] == 1.2


def test_transform_adage_time_object():
    result = transform_to_adage(MOCK_TLC_RECORDS)
    event = result["events"][0]
    assert event["time_object"]["duration"] == 23.5
    assert event["time_object"]["duration_unit"] == "minute"
    assert event["time_object"]["timezone"] == "America/New_York"


def test_transform_adage_timestamp_formatted():
    result = transform_to_adage(MOCK_TLC_RECORDS)
    ts = result["events"][0]["time_object"]["timestamp"]
    assert "T" not in ts
    assert " " in ts


def test_transform_adage_empty_records():
    result = transform_to_adage([])
    assert result["events"] == []
    assert result["data_source"] == "nyc_tlc"


def test_transform_adage_missing_fields():
    sparse_record = {
        "tpep_pickup_datetime": "2026-03-14T10:00:00.000",
        "tpep_dropoff_datetime": "2026-03-14T10:05:00.000",
    }
    result = transform_to_adage([sparse_record])
    attr = result["events"][0]["attribute"]
    assert attr["vendorid"] == 0
    assert attr["passenger_count"] == 0.0
    assert attr["trip_distance"] == 0.0
    assert attr["fare_amount"] == 0.0


def test_transform_adage_dataset_id_contains_s3():
    result = transform_to_adage(MOCK_TLC_RECORDS)
    assert result["dataset_id"].startswith("s3://")


# ── fetch_tlc_data ──────────────────────────────────────────────────────────

def test_fetch_tlc_data_calls_api():
    with patch("collectNYCTaxi.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_TLC_RECORDS,
            raise_for_status=lambda: None,
        )
        result = fetch_tlc_data(limit=100)

    mock_get.assert_called_once()
    call_args = mock_get.call_args
    assert "cityofnewyork.us" in call_args[0][0]
    assert len(result) == 2


def test_fetch_tlc_data_passes_limit():
    with patch("collectNYCTaxi.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_TLC_RECORDS,
            raise_for_status=lambda: None,
        )
        fetch_tlc_data(limit=500)

    params = mock_get.call_args[1]["params"]
    assert params["$limit"] == 500


def test_fetch_tlc_data_orders_by_pickup():
    with patch("collectNYCTaxi.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_TLC_RECORDS,
            raise_for_status=lambda: None,
        )
        fetch_tlc_data()

    params = mock_get.call_args[1]["params"]
    assert "DESC" in params["$order"]
    assert "tpep_pickup_datetime" in params["$order"]


# ── save_to_s3 ──────────────────────────────────────────────────────────────

@mock_aws
def test_save_to_s3_writes_correct_data(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=S3_BUCKET)

    save_to_s3({"test_key": "test_value"}, S3_BUCKET, "tlc/raw/test.json")

    obj = s3.get_object(Bucket=S3_BUCKET, Key="tlc/raw/test.json")
    body = json.loads(obj["Body"].read())
    assert body["test_key"] == "test_value"


@mock_aws
def test_save_to_s3_stores_valid_adage(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=S3_BUCKET)

    adage_data = transform_to_adage(MOCK_TLC_RECORDS)
    save_to_s3(adage_data, S3_BUCKET, "tlc/raw/adage_test.json")

    obj = s3.get_object(Bucket=S3_BUCKET, Key="tlc/raw/adage_test.json")
    stored = json.loads(obj["Body"].read())
    assert stored["data_source"] == "nyc_tlc"
    assert len(stored["events"]) == 2


# ── full pipeline ───────────────────────────────────────────────────────────

@mock_aws
def test_full_pipeline_fetch_transform_save(aws_credentials):
    """End-to-end: mock API call -> transform -> write to S3 -> verify."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=S3_BUCKET)

    with patch("collectNYCTaxi.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_TLC_RECORDS,
            raise_for_status=lambda: None,
        )
        raw = fetch_tlc_data(limit=2)

    adage_data = transform_to_adage(raw)
    save_to_s3(adage_data, S3_BUCKET, "tlc/raw/integration_test.json")

    obj = s3.get_object(Bucket=S3_BUCKET, Key="tlc/raw/integration_test.json")
    stored = json.loads(obj["Body"].read())

    assert stored["data_source"] == "nyc_tlc"
    assert len(stored["events"]) == 2
    assert stored["events"][0]["attribute"]["pulocationid"] == 161
    assert stored["events"][0]["time_object"]["duration"] == 23.5
    assert stored["events"][1]["attribute"]["trip_distance"] == 1.2
