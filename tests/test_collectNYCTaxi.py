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
    fetch_tlc_trips_lookback,
    calculate_duration_minutes,
    transform_to_adage,
    save_to_s3,
    S3_BUCKET,
)
from datetime import date as _date


# @pytest.fixture(autouse=True)
# def aws_credentials(monkeypatch):
#     monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
#     monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
#     monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


MOCK_TLC_RECORD_1 = {
    "vendorid": "2",
    "tpep_pickup_datetime": "2026-03-14T08:15:00.000",
    "tpep_dropoff_datetime": "2026-03-14T08:38:30.000",
    "passenger_count": "1",
    "trip_distance": "4.8",
    "pulocationid": "161",   # Manhattan - Midtown Center
    "dolocationid": "230",   # Manhattan - Times Sq/Theatre District
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
    "pulocationid": "237",   # Manhattan - Upper East Side South
    "dolocationid": "140",   # Manhattan - Lenox Hill East
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
    assert attr["pickup_locationid"] == 161
    assert attr["dropoff_locationid"] == 230
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
    assert attr["pickup_locationid"] == 237
    assert attr["dropoff_locationid"] == 140
    assert attr["passenger_count"] == 3.0
    assert attr["trip_distance"] == 1.2


# ── zone and borough lookup tests ────────────────────────────────────────────

def test_transform_adage_first_event_pickup_zone():
    # locationid 161 = Manhattan, Midtown Center
    result = transform_to_adage(MOCK_TLC_RECORDS)
    attr = result["events"][0]["attribute"]
    assert attr["pickup_borough"] == "Manhattan"
    assert attr["pickup_zone"] == "Midtown Center"


def test_transform_adage_first_event_dropoff_zone():
    # locationid 230 = Manhattan, Times Sq/Theatre District
    result = transform_to_adage(MOCK_TLC_RECORDS)
    attr = result["events"][0]["attribute"]
    assert attr["dropoff_borough"] == "Manhattan"
    assert attr["dropoff_zone"] == "Times Sq/Theatre District"


def test_transform_adage_second_event_pickup_zone():
    # locationid 237 = Manhattan, Upper East Side South
    result = transform_to_adage(MOCK_TLC_RECORDS)
    attr = result["events"][1]["attribute"]
    assert attr["pickup_borough"] == "Manhattan"
    assert attr["pickup_zone"] == "Upper East Side South"


def test_transform_adage_second_event_dropoff_zone():
    # locationid 140 = Manhattan, Lenox Hill East
    result = transform_to_adage(MOCK_TLC_RECORDS)
    attr = result["events"][1]["attribute"]
    assert attr["dropoff_borough"] == "Manhattan"
    assert attr["dropoff_zone"] == "Lenox Hill East"


def test_transform_adage_zone_fields_present():
    # All four zone/borough fields must exist on every event
    result = transform_to_adage(MOCK_TLC_RECORDS)
    for event in result["events"]:
        attr = event["attribute"]
        assert "pickup_zone" in attr
        assert "pickup_borough" in attr
        assert "dropoff_zone" in attr
        assert "dropoff_borough" in attr


def test_transform_adage_unknown_location_id():
    # locationid 0 is not in the lookup — should fall back to "Unknown"
    sparse_record = {
        "tpep_pickup_datetime": "2026-03-14T10:00:00.000",
        "tpep_dropoff_datetime": "2026-03-14T10:05:00.000",
        "pulocationid": "0",
        "dolocationid": "0",
    }
    result = transform_to_adage([sparse_record])
    attr = result["events"][0]["attribute"]
    assert attr["pickup_borough"] == "Unknown"
    assert attr["pickup_zone"] == "Unknown"
    assert attr["dropoff_borough"] == "Unknown"
    assert attr["dropoff_zone"] == "Unknown"


def test_transform_adage_airport_location():
    # locationid 132 = Queens, JFK Airport
    record = {**MOCK_TLC_RECORD_1, "pulocationid": "132", "dolocationid": "138"}
    result = transform_to_adage([record])
    attr = result["events"][0]["attribute"]
    assert attr["pickup_borough"] == "Queens"
    assert attr["pickup_zone"] == "JFK Airport"
    assert attr["dropoff_borough"] == "Queens"
    assert attr["dropoff_zone"] == "LaGuardia Airport"


def test_transform_adage_outer_borough_location():
    # locationid 11 = Brooklyn, Bath Beach
    record = {**MOCK_TLC_RECORD_1, "pulocationid": "11", "dolocationid": "55"}
    result = transform_to_adage([record])
    attr = result["events"][0]["attribute"]
    assert attr["pickup_borough"] == "Brooklyn"
    assert attr["pickup_zone"] == "Bath Beach"
    assert attr["dropoff_borough"] == "Brooklyn"
    assert attr["dropoff_zone"] == "Coney Island"


# ── transform_to_adage time object ──────────────────────────────────────────

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


# ── fetch_tlc_data (day-based) ───────────────────────────────────────────────

def test_fetch_tlc_data_calls_api():
    target = _date(2024, 6, 15)
    with patch("collectNYCTaxi.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_TLC_RECORDS,
            raise_for_status=lambda: None,
        )
        result = fetch_tlc_data(target, limit=100)

    mock_get.assert_called_once()
    call_args = mock_get.call_args
    assert "cityofnewyork.us" in call_args[0][0]
    assert len(result) == 2


def test_fetch_tlc_data_passes_limit():
    target = _date(2024, 6, 15)
    with patch("collectNYCTaxi.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_TLC_RECORDS,
            raise_for_status=lambda: None,
        )
        fetch_tlc_data(target, limit=500)

    params = mock_get.call_args[1]["params"]
    assert params["$limit"] == 500


def test_fetch_tlc_data_builds_day_where_clause():
    target = _date(2024, 6, 15)
    with patch("collectNYCTaxi.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_TLC_RECORDS,
            raise_for_status=lambda: None,
        )
        fetch_tlc_data(target)

    params = mock_get.call_args[1]["params"]
    assert "2024-06-15T00:00:00.000" in params["$where"]
    assert "2024-06-15T23:59:59.999" in params["$where"]


# ── fetch_tlc_trips_lookback (day-chunked) ───────────────────────────────────

def test_fetch_tlc_trips_lookback_calls_one_per_day():
    with patch("collectNYCTaxi._latest_dataset_date", return_value=_date(2024, 6, 20)):
        with patch("collectNYCTaxi.fetch_tlc_data_for_day", return_value=[{**MOCK_TLC_RECORD_1}]) as mock_day:
            out = fetch_tlc_trips_lookback(lookback_days=3, trips_per_day=10)

    assert mock_day.call_count == 3
    assert len(out) == 3


def test_fetch_tlc_trips_lookback_skips_failed_day():
    call_count = 0
    def side_effect(d, limit):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise Exception("timeout")
        return [{**MOCK_TLC_RECORD_1}]

    with patch("collectNYCTaxi._latest_dataset_date", return_value=_date(2024, 6, 20)):
        with patch("collectNYCTaxi.fetch_tlc_data_for_day", side_effect=side_effect):
            out = fetch_tlc_trips_lookback(lookback_days=3, trips_per_day=10)

    assert len(out) == 2   # 3 days, 1 skipped


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
        raw = fetch_tlc_data(_date(2024, 6, 15), limit=2)

    adage_data = transform_to_adage(raw)
    save_to_s3(adage_data, S3_BUCKET, "tlc/raw/integration_test.json")

    obj = s3.get_object(Bucket=S3_BUCKET, Key="tlc/raw/integration_test.json")
    stored = json.loads(obj["Body"].read())

    assert stored["data_source"] == "nyc_tlc"
    assert len(stored["events"]) == 2
    assert stored["events"][0]["attribute"]["pickup_locationid"] == 161
    assert stored["events"][0]["attribute"]["pickup_zone"] == "Midtown Center"
    assert stored["events"][0]["attribute"]["pickup_borough"] == "Manhattan"
    assert stored["events"][0]["attribute"]["dropoff_zone"] == "Times Sq/Theatre District"
    assert stored["events"][0]["time_object"]["duration"] == 23.5
    assert stored["events"][1]["attribute"]["trip_distance"] == 1.2

# ── Lambda Handler Tests ──────────────────────────────────────────────────────

@mock_aws
def test_lambda_handler_returns_200(aws_credentials):
    """lambda_handler returns HTTP 200 on a successful run."""
    from collectNYCTaxi import lambda_handler
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=S3_BUCKET)

    with patch("collectNYCTaxi.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_TLC_RECORDS,
            raise_for_status=lambda: None,
        )
        response = lambda_handler(event={}, context=None)

    assert response["statusCode"] == 200


@mock_aws
def test_lambda_handler_body_has_required_fields(aws_credentials):
    """lambda_handler response body contains message, records_collected, s3_location."""
    from collectNYCTaxi import lambda_handler
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=S3_BUCKET)

    with patch("collectNYCTaxi.requests.get") as mock_get:
        # First day returns 2 records; remaining 89 days return empty
        responses = []
        for i in range(90):
            responses.append(
                MagicMock(
                    json=lambda recs=(MOCK_TLC_RECORDS if i == 0 else []): recs,
                    raise_for_status=lambda: None,
                )
            )
        mock_get.side_effect = responses
        response = lambda_handler(event={}, context=None)


    import json
    body = json.loads(response["body"])
    assert "message" in body
    assert "records_collected" in body
    assert "s3_location" in body
    assert body["records_collected"] == 2
    assert body["s3_location"].startswith(f"s3://{S3_BUCKET}/")


@mock_aws
def test_lambda_handler_writes_valid_adage_to_s3(aws_credentials):
    """lambda_handler stores valid ADAGE 3.0 JSON with zone enrichment under tlc/raw."""
    from collectNYCTaxi import lambda_handler
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=S3_BUCKET)

    with patch("collectNYCTaxi.requests.get") as mock_get:
        # First day returns 2 records; remaining 89 days return empty
        responses = []
        for i in range(90):
            responses.append(
                MagicMock(
                    json=lambda recs=(MOCK_TLC_RECORDS if i == 0 else []): recs,
                    raise_for_status=lambda: None,
                )
            )
        mock_get.side_effect = responses
        response = lambda_handler(event={}, context=None)

    import json
    objects = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix="tlc/raw")
    keys = [obj["Key"] for obj in objects.get("Contents", [])]
    assert len(keys) >= 1

    stored = json.loads(s3.get_object(Bucket=S3_BUCKET, Key=keys[0])["Body"].read())
    assert stored["data_source"] == "nyc_tlc"
    assert stored["dataset_type"] == "taxi_trips"
    assert len(stored["events"]) == 2
    # Zone enrichment must survive the full pipeline
    assert stored["events"][0]["attribute"]["pickup_borough"] == "Manhattan"
    assert stored["events"][0]["attribute"]["pickup_zone"] == "Midtown Center"


@mock_aws
def test_lambda_handler_request_params(aws_credentials):
    """lambda_handler fetches with the correct $limit and $order parameters."""
    from collectNYCTaxi import lambda_handler
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=S3_BUCKET)

    with patch("collectNYCTaxi.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_TLC_RECORDS,
            raise_for_status=lambda: None,
        )
        lambda_handler(event={}, context=None)

    params = mock_get.call_args[1]["params"]
    assert "$limit" in params
    assert "tpep_pickup_datetime" in params["$order"]
    assert "DESC" in params["$order"]