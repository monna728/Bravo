"""Tests for the analytical model service.

All S3 and Prophet calls are mocked — no real AWS access or model training.
Tests cover: weather multipliers, time-of-day factors, normalisation,
contributing factors, fallback predictions, Prophet pipeline, handler
input validation, compare_all_boroughs, and response shapes.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import importlib.util

import pandas as pd
import boto3
from moto import mock_aws

import sys
import os

_model_dir = os.path.join(os.path.dirname(__file__), "..", "services", "analytical-model")
sys.path.insert(0, _model_dir)

from prophet_model import (
    get_weather_multiplier,
    get_time_of_day_factor,
    normalise_to_index,
    build_prophet_dataframe,
    calculate_contributing_factors,
    load_historical_data,
    predict,
    _fallback_predictions,
    VALID_BOROUGHS,
    WEATHER_MULTIPLIERS,
    TIME_OF_DAY_FACTORS,
    SIGNAL_WEIGHTS,
    MIN_DATAPOINTS,
)

_handler_spec = importlib.util.spec_from_file_location(
    "model_handler", os.path.join(_model_dir, "handler.py"))
_handler_mod = importlib.util.module_from_spec(_handler_spec)
_handler_spec.loader.exec_module(_handler_mod)
lambda_handler = _handler_mod.lambda_handler
_is_valid_date = _handler_mod._is_valid_date
_parse_body = _handler_mod._parse_body

BUCKET = "test-bucket"


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


def _make_merged_adage(records: list[dict]) -> dict:
    """Build a mock ADAGE dict with merged daily demand events."""
    events = []
    for r in records:
        events.append({
            "time_object": {
                "timestamp": f"{r['date']} 00:00:00.000000",
                "duration": 24,
                "duration_unit": "hour",
                "timezone": "America/New_York",
            },
            "event_type": "daily_demand_features",
            "attribute": r,
        })
    return {
        "data_source": "merged",
        "dataset_type": "demand_features",
        "dataset_id": f"s3://{BUCKET}/processed/merged/test.json",
        "time_object": {"timestamp": "2026-03-15 10:00:00.000000", "timezone": "America/New_York"},
        "events": events,
    }


def _generate_daily_records(borough: str, num_days: int = 30, base_date: str = "2026-01-01") -> list[dict]:
    """Generate a series of mock merged daily records for testing."""
    start = datetime.strptime(base_date, "%Y-%m-%d")
    records = []
    for i in range(num_days):
        d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        records.append({
            "date": d,
            "borough": borough,
            "trip_count": 3000 + (i * 100),
            "event_count": 2 + (i % 5),
            "total_expected_attendance": 5000,
            "event_names": ["Test Event"],
            "avg_trip_distance_miles": 3.5,
            "avg_fare_amount": 15.0,
            "avg_trip_duration_min": 12.0,
            "total_passengers": 4500 + (i * 50),
            "temperature_avg_c": 10.0 + (i * 0.3),
            "temperature_max_c": 15.0 + (i * 0.3),
            "temperature_min_c": 5.0 + (i * 0.3),
            "precipitation_total_mm": 0.5 if i % 3 == 0 else 0.0,
            "avg_demand_modifier": 1.0,
            "dominant_weather": "clear" if i % 4 != 0 else "rain",
            "sources_present": ["ticketmaster", "nyc_tlc", "open_meteo"],
        })
    return records


# ── Weather Multipliers ─────────────────────────────────────────────────────

def test_weather_multiplier_thunderstorm():
    assert get_weather_multiplier("thunderstorm") == 0.75


def test_weather_multiplier_snow():
    assert get_weather_multiplier("snow") == 0.75


def test_weather_multiplier_rain():
    assert get_weather_multiplier("rain") == 0.85


def test_weather_multiplier_showers():
    assert get_weather_multiplier("showers") == 0.85


def test_weather_multiplier_fog():
    assert get_weather_multiplier("fog") == 0.92


def test_weather_multiplier_clear():
    assert get_weather_multiplier("clear") == 1.0


def test_weather_multiplier_cloudy():
    assert get_weather_multiplier("cloudy") == 1.0


def test_weather_multiplier_unknown():
    assert get_weather_multiplier("unknown") == 1.0


def test_weather_multiplier_case_insensitive():
    assert get_weather_multiplier("RAIN") == 0.85
    assert get_weather_multiplier("Thunderstorm") == 0.75


def test_weather_multiplier_empty_string():
    assert get_weather_multiplier("") == 1.0


def test_weather_multiplier_none():
    assert get_weather_multiplier(None) == 1.0


# ── Time of Day Factors ─────────────────────────────────────────────────────

def test_tod_morning():
    assert get_time_of_day_factor("morning") == 0.7


def test_tod_afternoon():
    assert get_time_of_day_factor("afternoon") == 0.9


def test_tod_evening():
    assert get_time_of_day_factor("evening") == 1.15


def test_tod_night():
    assert get_time_of_day_factor("night") == 0.6


def test_tod_all():
    assert get_time_of_day_factor("all") == 1.0


def test_tod_case_insensitive():
    assert get_time_of_day_factor("EVENING") == 1.15


def test_tod_invalid():
    assert get_time_of_day_factor("midnight") == 1.0


# ── Normalise to Index ──────────────────────────────────────────────────────

def test_normalise_basic():
    historical = [1000.0, 2000.0, 3000.0, 4000.0, 5000.0]
    predictions = [3000.0]
    result = normalise_to_index(predictions, historical)
    assert result == [50.0]


def test_normalise_at_max():
    historical = [1000.0, 5000.0]
    result = normalise_to_index([5000.0], historical)
    assert result == [100.0]


def test_normalise_at_min():
    historical = [1000.0, 5000.0]
    result = normalise_to_index([1000.0], historical)
    assert result == [0.0]


def test_normalise_above_max_clamped():
    historical = [1000.0, 5000.0]
    result = normalise_to_index([10000.0], historical)
    assert result == [100.0]


def test_normalise_below_min_clamped():
    historical = [1000.0, 5000.0]
    result = normalise_to_index([0.0], historical)
    assert result == [0.0]


def test_normalise_empty_history():
    result = normalise_to_index([3000.0], [])
    assert result == [50.0]


def test_normalise_same_min_max():
    result = normalise_to_index([5000.0], [5000.0, 5000.0])
    assert result == [50.0]


def test_normalise_multiple_values():
    historical = [0.0, 100.0]
    result = normalise_to_index([25.0, 50.0, 75.0], historical)
    assert result == [25.0, 50.0, 75.0]


# ── Build Prophet DataFrame ─────────────────────────────────────────────────

def test_build_dataframe_columns():
    records = _generate_daily_records("Manhattan", 5)
    df = build_prophet_dataframe(records)
    assert "ds" in df.columns
    assert "y" in df.columns
    assert "event_count" in df.columns
    assert "is_rainy" in df.columns
    assert "temperature_c" in df.columns
    assert "dominant_weather" in df.columns
    assert "active_events" in df.columns


def test_build_dataframe_row_count():
    records = _generate_daily_records("Brooklyn", 10)
    df = build_prophet_dataframe(records)
    assert len(df) == 10


def test_build_dataframe_y_is_trip_count():
    records = [{"date": "2026-01-01", "trip_count": 4200, "event_count": 3,
                "dominant_weather": "clear", "temperature_avg_c": 12.0}]
    df = build_prophet_dataframe(records)
    assert df["y"].iloc[0] == 4200.0


def test_build_dataframe_is_rainy_flag():
    records = [
        {"date": "2026-01-01", "trip_count": 100, "event_count": 1,
         "dominant_weather": "rain", "temperature_avg_c": 10.0},
        {"date": "2026-01-02", "trip_count": 100, "event_count": 1,
         "dominant_weather": "clear", "temperature_avg_c": 10.0},
    ]
    df = build_prophet_dataframe(records)
    assert df["is_rainy"].iloc[0] == 1.0
    assert df["is_rainy"].iloc[1] == 0.0


def test_build_dataframe_empty():
    df = build_prophet_dataframe([])
    assert len(df) == 0


# ── Contributing Factors ────────────────────────────────────────────────────

def test_contributing_factors_basic():
    records = _generate_daily_records("Manhattan", 10)
    df = build_prophet_dataframe(records)
    factors = calculate_contributing_factors(records, df)

    assert "taxi_signal" in factors
    assert "event_signal" in factors
    assert "weather_impact" in factors
    assert "active_events" in factors
    assert 0.0 <= factors["taxi_signal"] <= 1.0
    assert 0.0 <= factors["event_signal"] <= 1.0


def test_contributing_factors_empty():
    df = pd.DataFrame()
    factors = calculate_contributing_factors([], df)
    assert factors["taxi_signal"] == 0.0
    assert factors["event_signal"] == 0.0
    assert factors["weather_impact"] == 1.0
    assert factors["active_events"] == 0


def test_contributing_factors_weather_impact():
    records = [{"date": "2026-01-01", "trip_count": 100, "event_count": 1,
                "dominant_weather": "thunderstorm", "temperature_avg_c": 10.0}]
    df = build_prophet_dataframe(records)
    factors = calculate_contributing_factors(records, df)
    assert factors["weather_impact"] == 0.75


# ── Fallback Predictions ────────────────────────────────────────────────────

def test_fallback_single_day():
    preds = _fallback_predictions("2026-04-15", "2026-04-15", "all")
    assert len(preds) == 1
    assert preds[0]["date"] == "2026-04-15"
    assert preds[0]["demand_index"] == 50.0


def test_fallback_multi_day():
    preds = _fallback_predictions("2026-04-15", "2026-04-17", "evening")
    assert len(preds) == 3
    for p in preds:
        assert p["demand_index"] == 50.0
        assert p["time_of_day"] == "evening"
        assert p["weather_condition"] == "unknown"


# ── Valid Boroughs ───────────────────────────────────────────────────────────

def test_valid_boroughs_count():
    assert len(VALID_BOROUGHS) == 5


def test_signal_weights_sum_to_one():
    assert sum(SIGNAL_WEIGHTS.values()) == pytest.approx(1.0)


# ── Load Historical Data (S3 integration) ───────────────────────────────────

@mock_aws
def test_load_historical_data_filters_by_borough(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)

    manhattan_records = _generate_daily_records("Manhattan", 10, "2026-01-01")
    brooklyn_records = _generate_daily_records("Brooklyn", 5, "2026-01-01")
    all_records = manhattan_records + brooklyn_records

    adage = _make_merged_adage(all_records)
    s3.put_object(Bucket=BUCKET, Key="processed/merged/test.json",
                  Body=json.dumps(adage), ContentType="application/json")

    result = load_historical_data("Manhattan", bucket=BUCKET, end_date="2026-02-01")
    assert len(result) == 10
    for r in result:
        assert r["borough"] == "Manhattan"


@mock_aws
def test_load_historical_data_date_window(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)

    records = _generate_daily_records("Manhattan", 120, "2025-09-01")
    adage = _make_merged_adage(records)
    s3.put_object(Bucket=BUCKET, Key="processed/merged/test.json",
                  Body=json.dumps(adage), ContentType="application/json")

    result = load_historical_data("Manhattan", bucket=BUCKET, lookback_days=30, end_date="2025-12-30")
    for r in result:
        assert r["date"] >= "2025-11-30"
        assert r["date"] <= "2025-12-30"


@mock_aws
def test_load_historical_data_empty_bucket(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)

    result = load_historical_data("Manhattan", bucket=BUCKET, end_date="2026-02-01")
    assert result == []


# ── Predict (mocked Prophet) ────────────────────────────────────────────────

@mock_aws
def test_predict_insufficient_data_returns_warning(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)

    result = predict(
        borough="Manhattan",
        start_date="2026-04-15",
        end_date="2026-04-17",
        bucket=BUCKET,
    )
    assert result["status"] == "warning"
    assert "Insufficient" in result["message"]
    assert len(result["predictions"]) == 3


@mock_aws
@patch("prophet_model.fit_and_forecast")
def test_predict_success_with_mocked_prophet(mock_forecast, aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)

    records = _generate_daily_records("Manhattan", 30, "2026-01-01")
    adage = _make_merged_adage(records)
    s3.put_object(Bucket=BUCKET, Key="processed/merged/test.json",
                  Body=json.dumps(adage), ContentType="application/json")

    mock_forecast.return_value = pd.DataFrame({
        "ds": pd.to_datetime(["2026-04-15", "2026-04-16"]),
        "yhat": [4000.0, 4200.0],
        "yhat_lower": [3500.0, 3700.0],
        "yhat_upper": [4500.0, 4700.0],
    })

    result = predict(
        borough="Manhattan",
        start_date="2026-04-15",
        end_date="2026-04-16",
        bucket=BUCKET,
    )

    assert result["status"] == "success"
    assert result["borough"] == "Manhattan"
    assert len(result["predictions"]) == 2
    assert "demand_index" in result["predictions"][0]
    assert "contributing_factors" in result
    assert "model_info" in result


@mock_aws
@patch("prophet_model.fit_and_forecast")
def test_predict_evening_applies_tod_factor(mock_forecast, aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)

    records = _generate_daily_records("Brooklyn", 30, "2026-01-01")
    adage = _make_merged_adage(records)
    s3.put_object(Bucket=BUCKET, Key="processed/merged/test.json",
                  Body=json.dumps(adage), ContentType="application/json")

    mock_forecast.return_value = pd.DataFrame({
        "ds": pd.to_datetime(["2026-04-15"]),
        "yhat": [4000.0],
        "yhat_lower": [3500.0],
        "yhat_upper": [4500.0],
    })

    result_all = predict(borough="Brooklyn", start_date="2026-04-15",
                         end_date="2026-04-15", time_of_day="all", bucket=BUCKET)
    result_eve = predict(borough="Brooklyn", start_date="2026-04-15",
                         end_date="2026-04-15", time_of_day="evening", bucket=BUCKET)

    score_all = result_all["predictions"][0]["demand_index"]
    score_eve = result_eve["predictions"][0]["demand_index"]
    assert score_eve >= score_all


@mock_aws
@patch("prophet_model.fit_and_forecast")
def test_predict_response_shape(mock_forecast, aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)

    records = _generate_daily_records("Queens", 30, "2026-01-01")
    adage = _make_merged_adage(records)
    s3.put_object(Bucket=BUCKET, Key="processed/merged/test.json",
                  Body=json.dumps(adage), ContentType="application/json")

    mock_forecast.return_value = pd.DataFrame({
        "ds": pd.to_datetime(["2026-04-15"]),
        "yhat": [3500.0],
        "yhat_lower": [3000.0],
        "yhat_upper": [4000.0],
    })

    result = predict(borough="Queens", start_date="2026-04-15",
                     end_date="2026-04-15", bucket=BUCKET)

    assert "status" in result
    assert "borough" in result
    assert "predictions" in result
    assert "contributing_factors" in result
    assert "model_info" in result

    pred = result["predictions"][0]
    assert "date" in pred
    assert "demand_index" in pred
    assert "confidence_lower" in pred
    assert "confidence_upper" in pred
    assert "time_of_day" in pred
    assert "weather_condition" in pred
    assert "weather_multiplier" in pred

    factors = result["contributing_factors"]
    assert "taxi_signal" in factors
    assert "event_signal" in factors
    assert "weather_impact" in factors
    assert "active_events" in factors


@mock_aws
@patch("prophet_model.fit_and_forecast")
def test_predict_demand_index_clamped_0_100(mock_forecast, aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)

    records = _generate_daily_records("Bronx", 30, "2026-01-01")
    adage = _make_merged_adage(records)
    s3.put_object(Bucket=BUCKET, Key="processed/merged/test.json",
                  Body=json.dumps(adage), ContentType="application/json")

    mock_forecast.return_value = pd.DataFrame({
        "ds": pd.to_datetime(["2026-04-15"]),
        "yhat": [99999.0],
        "yhat_lower": [-5000.0],
        "yhat_upper": [99999.0],
    })

    result = predict(borough="Bronx", start_date="2026-04-15",
                     end_date="2026-04-15", bucket=BUCKET)

    assert result["predictions"][0]["demand_index"] <= 100.0
    assert result["predictions"][0]["demand_index"] >= 0.0


@mock_aws
@patch("prophet_model.fit_and_forecast")
def test_predict_prophet_error_returns_fallback(mock_forecast, aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)

    records = _generate_daily_records("Manhattan", 30, "2026-01-01")
    adage = _make_merged_adage(records)
    s3.put_object(Bucket=BUCKET, Key="processed/merged/test.json",
                  Body=json.dumps(adage), ContentType="application/json")

    mock_forecast.side_effect = RuntimeError("Prophet crashed")

    result = predict(borough="Manhattan", start_date="2026-04-15",
                     end_date="2026-04-15", bucket=BUCKET)

    assert result["status"] == "error"
    assert "Prophet" in result["message"]
    assert len(result["predictions"]) == 1
    assert result["predictions"][0]["demand_index"] == 50.0


# ── Handler Validation ──────────────────────────────────────────────────────

def test_handler_missing_borough():
    event = {"body": json.dumps({"start_date": "2026-04-15", "end_date": "2026-04-17"})}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "borough is required" in body["error"]


def test_handler_missing_start_date():
    event = {"body": json.dumps({"borough": "Manhattan", "end_date": "2026-04-17"})}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    assert "start_date" in json.loads(response["body"])["error"]


def test_handler_missing_end_date():
    event = {"body": json.dumps({"borough": "Manhattan", "start_date": "2026-04-15"})}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    assert "end_date" in json.loads(response["body"])["error"]


def test_handler_invalid_borough():
    event = {"body": json.dumps({
        "borough": "Hoboken", "start_date": "2026-04-15", "end_date": "2026-04-17"
    })}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    assert "Invalid borough" in json.loads(response["body"])["error"]


def test_handler_invalid_time_of_day():
    event = {"body": json.dumps({
        "borough": "Manhattan", "start_date": "2026-04-15",
        "end_date": "2026-04-17", "time_of_day": "midnight"
    })}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    assert "Invalid time_of_day" in json.loads(response["body"])["error"]


def test_handler_invalid_date_format():
    event = {"body": json.dumps({
        "borough": "Manhattan", "start_date": "15-04-2026", "end_date": "2026-04-17"
    })}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    assert "Invalid start_date" in json.loads(response["body"])["error"]


def test_handler_start_after_end():
    event = {"body": json.dumps({
        "borough": "Manhattan", "start_date": "2026-04-20", "end_date": "2026-04-15"
    })}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    assert "start_date must be before" in json.loads(response["body"])["error"]


def test_handler_invalid_json_body():
    event = {"body": "not json at all"}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    assert "Invalid JSON" in json.loads(response["body"])["error"]


@mock_aws
def test_handler_success_returns_200(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)

    event = {"body": json.dumps({
        "borough": "Manhattan",
        "start_date": "2026-04-15",
        "end_date": "2026-04-17",
        "bucket": BUCKET,
    })}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["borough"] == "Manhattan"


@mock_aws
@patch("prophet_model.fit_and_forecast")
def test_handler_compare_all_boroughs(mock_forecast, aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)

    all_records = []
    for borough in VALID_BOROUGHS:
        all_records.extend(_generate_daily_records(borough, 10, "2026-01-01"))
    adage = _make_merged_adage(all_records)
    s3.put_object(Bucket=BUCKET, Key="processed/merged/test.json",
                  Body=json.dumps(adage), ContentType="application/json")

    mock_forecast.return_value = pd.DataFrame({
        "ds": pd.to_datetime(["2026-04-15"]),
        "yhat": [3500.0],
        "yhat_lower": [3000.0],
        "yhat_upper": [4000.0],
    })

    event = {"body": json.dumps({
        "compare_all_boroughs": True,
        "start_date": "2026-04-15",
        "end_date": "2026-04-15",
        "bucket": BUCKET,
    })}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["compare_all_boroughs"] is True
    assert "boroughs" in body
    assert len(body["boroughs"]) == 5
    for borough_name in VALID_BOROUGHS:
        assert borough_name in body["boroughs"]


@mock_aws
def test_handler_direct_invocation(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)

    event = {
        "borough": "Manhattan",
        "start_date": "2026-04-15",
        "end_date": "2026-04-17",
        "bucket": BUCKET,
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200


# ── Helper Functions ─────────────────────────────────────────────────────────

def test_is_valid_date_good():
    assert _is_valid_date("2026-04-15") is True


def test_is_valid_date_bad_format():
    assert _is_valid_date("15-04-2026") is False


def test_is_valid_date_too_short():
    assert _is_valid_date("2026-04") is False


def test_is_valid_date_empty():
    assert _is_valid_date("") is False


def test_parse_body_json_string():
    event = {"body": '{"borough": "Manhattan"}'}
    result = _parse_body(event)
    assert result["borough"] == "Manhattan"


def test_parse_body_dict():
    event = {"body": {"borough": "Brooklyn"}}
    result = _parse_body(event)
    assert result["borough"] == "Brooklyn"


def test_parse_body_direct():
    event = {"borough": "Queens"}
    result = _parse_body(event)
    assert result["borough"] == "Queens"


def test_parse_body_invalid_json():
    event = {"body": "not json"}
    with pytest.raises(ValueError, match="Invalid JSON"):
        _parse_body(event)
