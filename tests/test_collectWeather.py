import json
import pytest
import boto3
from moto import mock_aws
from unittest.mock import patch, MagicMock

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "data-collection"))
from collectWeather import (
    fetch_weather_data,
    compute_demand_modifier,
    classify_weather,
    transform_to_adage,
    save_to_s3,
    S3_BUCKET,
)

# @pytest.fixture(autouse=True)
# def aws_credentials(monkeypatch):
#     monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
#     monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
#     monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


MOCK_OPEN_METEO_RESPONSE = {
    "latitude": 40.7128,
    "longitude": -74.006,
    "timezone": "America/New_York",
    "hourly": {
        "time": [
            "2026-02-01T00:00",
            "2026-02-01T08:00",
            "2026-02-01T17:00",
            "2026-02-01T22:00",
        ],
        "precipitation":             [0.0,  3.5,  0.0,  7.2],
        "temperature_2m":            [20.0, 14.0, 18.0, 3.0],
        "precipitation_probability": [0,    60,   0,    90],
    },
}

def test_demand_modifier_dry_mild():
    assert compute_demand_modifier(0.0, 20.0) == 1.0

def test_demand_modifier_drizzle():
    assert compute_demand_modifier(0.5, 20.0) == 1.05

def test_demand_modifier_light_rain():
    assert compute_demand_modifier(2.0, 20.0) == 1.15

def test_demand_modifier_heavy_rain():
    assert compute_demand_modifier(6.0, 20.0) == 1.30

def test_demand_modifier_very_cold():
    assert compute_demand_modifier(0.0, 2.0) == 1.10

def test_demand_modifier_heavy_rain_and_cold():
    # 7.2mm rain + 3°C cold → 1.30 + 0.10
    assert compute_demand_modifier(7.2, 3.0) == 1.40

def test_demand_modifier_very_hot():
    assert compute_demand_modifier(0.0, 38.0) == 1.05

def test_demand_modifier_rounded_to_2dp():
    result = compute_demand_modifier(2.0, 2.0)
    assert result == round(result, 2)


# ── Unit Tests: classify_weather ──────────────────────────────────────────────

def test_classify_clear():
    assert classify_weather(0.0) == "clear"

def test_classify_drizzle():
    assert classify_weather(0.5) == "drizzle"

def test_classify_light_rain():
    assert classify_weather(2.0) == "light_rain"

def test_classify_heavy_rain():
    assert classify_weather(7.0) == "heavy_rain"

def test_classify_extreme():
    assert classify_weather(15.0) == "extreme"

def test_transform_adage_structure():
    result = transform_to_adage(MOCK_OPEN_METEO_RESPONSE)
    assert result["data_source"] == "open_meteo"
    assert result["dataset_type"] == "weather_forecast"
    assert "time_object" in result
    assert "events" in result

def test_transform_adage_event_count():
    result = transform_to_adage(MOCK_OPEN_METEO_RESPONSE)
    assert len(result["events"]) == 4

def test_transform_adage_event_type():
    result = transform_to_adage(MOCK_OPEN_METEO_RESPONSE)
    for event in result["events"]:
        assert event["event_type"] == "weather_forecast"

def test_transform_adage_event_has_required_fields():
    result = transform_to_adage(MOCK_OPEN_METEO_RESPONSE)
    event = result["events"][0]
    assert "time_object" in event
    assert "attribute" in event
    attr = event["attribute"]
    assert "precipitation_mm" in attr
    assert "temperature_c" in attr
    assert "demand_modifier" in attr
    assert "weather_category" in attr

def test_transform_adage_demand_modifiers_correct():
    result = transform_to_adage(MOCK_OPEN_METEO_RESPONSE)
    events = result["events"]
    assert events[0]["attribute"]["demand_modifier"] == 1.0
    assert events[1]["attribute"]["demand_modifier"] == 1.15
    assert events[3]["attribute"]["demand_modifier"] == 1.40

def test_transform_adage_weather_categories_correct():
    result = transform_to_adage(MOCK_OPEN_METEO_RESPONSE)
    events = result["events"]
    assert events[0]["attribute"]["weather_category"] == "clear"
    assert events[1]["attribute"]["weather_category"] == "light_rain"
    assert events[3]["attribute"]["weather_category"] == "heavy_rain"

def test_transform_adage_time_object_per_event():
    result = transform_to_adage(MOCK_OPEN_METEO_RESPONSE)
    event = result["events"][0]
    assert event["time_object"]["timestamp"] == "2026-02-01T00:00"
    assert event["time_object"]["duration"] == 1
    assert event["time_object"]["duration_unit"] == "hour"

def test_transform_adage_empty_response():
    result = transform_to_adage({"hourly": {"time": [], "precipitation": [], "temperature_2m": [], "precipitation_probability": []}})
    assert result["events"] == []

def test_fetch_weather_data_calls_open_meteo():
    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_OPEN_METEO_RESPONSE,
            raise_for_status=lambda: None,
        )
        result = fetch_weather_data(lat=40.7128, lng=-74.006, forecast_days=7)

    mock_get.assert_called_once()
    call_args = mock_get.call_args
    assert "api.open-meteo.com" in call_args[0][0]
    assert result["latitude"] == 40.7128

def test_fetch_weather_data_passes_correct_params():
    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_OPEN_METEO_RESPONSE,
            raise_for_status=lambda: None,
        )
        fetch_weather_data(lat=40.7128, lng=-74.006, forecast_days=3)

    params = mock_get.call_args[1]["params"]
    assert params["latitude"] == 40.7128
    assert params["longitude"] == -74.006
    assert params["forecast_days"] == 3
    assert "precipitation" in params["hourly"]
    assert "temperature_2m" in params["hourly"]

@mock_aws
def test_save_to_s3_writes_correct_data(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=S3_BUCKET)

    save_to_s3({"test_key": "test_value"}, S3_BUCKET, "weather/raw/test.json")

    obj = s3.get_object(Bucket=S3_BUCKET, Key="weather/raw/test.json")
    body = json.loads(obj["Body"].read())
    assert body["test_key"] == "test_value"

@mock_aws
def test_save_to_s3_stores_valid_json(aws_credentials):
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=S3_BUCKET)

    adage_data = transform_to_adage(MOCK_OPEN_METEO_RESPONSE)
    save_to_s3(adage_data, S3_BUCKET, "weather/raw/adage_test.json")

    obj = s3.get_object(Bucket=S3_BUCKET, Key="weather/raw/adage_test.json")
    stored = json.loads(obj["Body"].read())
    assert stored["data_source"] == "open_meteo"
    assert len(stored["events"]) == 4

@mock_aws
def test_full_pipeline_fetch_transform_save(aws_credentials):
    """Full end-to-end: mock API call → transform → write to S3 → verify."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=S3_BUCKET)

    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_OPEN_METEO_RESPONSE,
            raise_for_status=lambda: None,
        )
        raw = fetch_weather_data(forecast_days=7)

    adage_data = transform_to_adage(raw)
    save_to_s3(adage_data, S3_BUCKET, "weather/raw/integration_test.json")

    obj = s3.get_object(Bucket=S3_BUCKET, Key="weather/raw/integration_test.json")
    stored = json.loads(obj["Body"].read())

    assert stored["data_source"] == "open_meteo"
    assert len(stored["events"]) == 4
    assert stored["events"][3]["attribute"]["demand_modifier"] == 1.40
    assert stored["events"][0]["attribute"]["weather_category"] == "clear"

# ── Lambda Handler Tests ──────────────────────────────────────────────────────

@mock_aws
def test_lambda_handler_returns_200(aws_credentials):
    """lambda_handler returns HTTP 200 on a successful run."""
    from collectWeather import lambda_handler
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=S3_BUCKET)

    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_OPEN_METEO_RESPONSE,
            raise_for_status=lambda: None,
        )
        response = lambda_handler(event={}, context=None)

    assert response["statusCode"] == 200


@mock_aws
def test_lambda_handler_body_has_required_fields(aws_credentials):
    """lambda_handler response body contains message, records_collected, s3_location."""
    from collectWeather import lambda_handler
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=S3_BUCKET)

    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_OPEN_METEO_RESPONSE,
            raise_for_status=lambda: None,
        )
        response = lambda_handler(event={}, context=None)

    import json
    body = json.loads(response["body"])
    assert "message" in body
    assert "records_collected" in body
    assert "s3_location" in body
    assert body["records_collected"] == 4
    assert body["s3_location"].startswith(f"s3://{S3_BUCKET}/")


@mock_aws
def test_lambda_handler_writes_valid_adage_to_s3(aws_credentials):
    """lambda_handler stores valid ADAGE 3.0 JSON under the weather/raw prefix."""
    from collectWeather import lambda_handler
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=S3_BUCKET)

    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_OPEN_METEO_RESPONSE,
            raise_for_status=lambda: None,
        )
        lambda_handler(event={}, context=None)

    import json
    objects = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix="weather/raw")
    keys = [obj["Key"] for obj in objects.get("Contents", [])]
    assert len(keys) >= 1

    stored = json.loads(s3.get_object(Bucket=S3_BUCKET, Key=keys[0])["Body"].read())
    assert stored["data_source"] == "open_meteo"
    assert stored["dataset_type"] == "weather_forecast"
    assert len(stored["events"]) == 4


@mock_aws
def test_lambda_handler_uses_custom_lat_lng(aws_credentials):
    """lambda_handler passes custom lat/lng from the event dict to the API."""
    from collectWeather import lambda_handler
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=S3_BUCKET)

    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: MOCK_OPEN_METEO_RESPONSE,
            raise_for_status=lambda: None,
        )
        lambda_handler(event={"lat": 51.5074, "lng": -0.1278}, context=None)

    params = mock_get.call_args[1]["params"]
    assert params["latitude"] == 51.5074
    assert params["longitude"] == -0.1278

# # ── Lambda Handler Tests ──────────────────────────────────────────────────────
# # tests the full Lambda entry point end-to-end, completing the
# # component-level coverage: fetch → transform → S3 → response shape.

# import json
# import boto3
# from moto import mock_aws
# from unittest.mock import patch, MagicMock

# # (These imports already exist in test_collectWeather.py — shown here for clarity)
# # from collectWeather import lambda_handler, S3_BUCKET, MOCK_OPEN_METEO_RESPONSE

# @mock_aws
# def test_lambda_handler_returns_200_on_success(aws_credentials):
#     """Lambda handler completes successfully and returns HTTP 200."""
#     s3 = boto3.client("s3", region_name="us-east-1")
#     s3.create_bucket(Bucket=S3_BUCKET)

#     with patch("requests.get") as mock_get:
#         mock_get.return_value = MagicMock(
#             json=lambda: MOCK_OPEN_METEO_RESPONSE,
#             raise_for_status=lambda: None,
#         )
#         response = lambda_handler(event={}, context=None)

#     assert response["statusCode"] == 200


# @mock_aws
# def test_lambda_handler_response_body_structure(aws_credentials):
#     """Lambda handler response body contains expected fields."""
#     s3 = boto3.client("s3", region_name="us-east-1")
#     s3.create_bucket(Bucket=S3_BUCKET)

#     with patch("requests.get") as mock_get:
#         mock_get.return_value = MagicMock(
#             json=lambda: MOCK_OPEN_METEO_RESPONSE,
#             raise_for_status=lambda: None,
#         )
#         response = lambda_handler(event={}, context=None)

#     body = json.loads(response["body"])
#     assert "message" in body
#     assert "records_collected" in body
#     assert "s3_location" in body
#     assert body["records_collected"] == 4  # MOCK_OPEN_METEO_RESPONSE has 4 hourly slots
#     assert body["s3_location"].startswith(f"s3://{S3_BUCKET}/")


# @mock_aws
# def test_lambda_handler_writes_adage_data_to_s3(aws_credentials):
#     """Lambda handler persists valid ADAGE 3.0 JSON to S3."""
#     s3 = boto3.client("s3", region_name="us-east-1")
#     s3.create_bucket(Bucket=S3_BUCKET)

#     with patch("requests.get") as mock_get:
#         mock_get.return_value = MagicMock(
#             json=lambda: MOCK_OPEN_METEO_RESPONSE,
#             raise_for_status=lambda: None,
#         )
#         lambda_handler(event={}, context=None)

#     # Verify at least one object was written under the expected prefix
#     objects = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix="weather/raw")
#     keys = [obj["Key"] for obj in objects.get("Contents", [])]
#     assert len(keys) >= 1

#     # Verify the stored data is valid ADAGE 3.0 JSON
#     stored_data = json.loads(s3.get_object(Bucket=S3_BUCKET, Key=keys[0])["Body"].read())
#     assert stored_data["data_source"] == "open_meteo"
#     assert stored_data["dataset_type"] == "weather_forecast"
#     assert "events" in stored_data
#     assert len(stored_data["events"]) == 4


# @mock_aws
# def test_lambda_handler_accepts_custom_lat_lng(aws_credentials):
#     """Lambda handler passes custom lat/lng from the event to the API call."""
#     s3 = boto3.client("s3", region_name="us-east-1")
#     s3.create_bucket(Bucket=S3_BUCKET)

#     with patch("requests.get") as mock_get:
#         mock_get.return_value = MagicMock(
#             json=lambda: MOCK_OPEN_METEO_RESPONSE,
#             raise_for_status=lambda: None,
#         )
#         lambda_handler(event={"lat": 51.5074, "lng": -0.1278}, context=None)

#     params = mock_get.call_args[1]["params"]
#     assert params["latitude"] == 51.5074
#     assert params["longitude"] == -0.1278