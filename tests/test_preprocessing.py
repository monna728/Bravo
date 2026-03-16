import json
import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "data-preprocessing"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services"))

from normaliser import normalise_ticketmaster, normalise_nyc_taxi, normalise_weather
from merger import merge_by_date, merged_to_adage
from shared.adage_validator import validate_adage3


# ── Mock ADAGE data from each collector ──────────────────────────────────────

MOCK_TICKETMASTER_ADAGE = {
    "data_source": "ticketmaster",
    "dataset_type": "public_events",
    "dataset_id": "s3://bucket/ticketmaster/raw/test.json",
    "time_object": {"timestamp": "2026-03-15 10:00:00.000000", "timezone": "America/New_York"},
    "events": [
        {
            "time_object": {"timestamp": "2026-04-15T19:00:00Z", "duration": 0, "duration_unit": "hour", "timezone": "America/New_York"},
            "event_type": "concert",
            "attribute": {"event_id": "e1", "event_name": "Rock Concert", "venue_name": "MSG", "latitude": 40.75, "longitude": -73.99},
        },
        {
            "time_object": {"timestamp": "2026-04-15T21:00:00Z", "duration": 0, "duration_unit": "hour", "timezone": "America/New_York"},
            "event_type": "sports",
            "attribute": {"event_id": "e2", "event_name": "Knicks Game", "venue_name": "MSG", "latitude": 40.75, "longitude": -73.99},
        },
        {
            "time_object": {"timestamp": "2026-04-16T20:00:00Z", "duration": 0, "duration_unit": "hour", "timezone": "America/New_York"},
            "event_type": "concert",
            "attribute": {"event_id": "e3", "event_name": "Jazz Night", "venue_name": "Blue Note", "latitude": 40.73, "longitude": -74.0},
        },
    ],
}

MOCK_TAXI_ADAGE = {
    "data_source": "nyc_tlc",
    "dataset_type": "taxi_trips",
    "dataset_id": "s3://bucket/tlc/raw/test.json",
    "time_object": {"timestamp": "2026-03-15 10:00:00.000000", "timezone": "America/New_York"},
    "events": [
        {
            "time_object": {"timestamp": "2026-04-15 08:15:00.000000", "duration": 23.5, "duration_unit": "minute", "timezone": "America/New_York"},
            "event_type": "taxi_pickup",
            "attribute": {"vendorid": 2, "pickup_locationid": 161, "pickup_zone": "Midtown Center", "pickup_borough": "Manhattan", "dropoff_locationid": 230, "dropoff_zone": "Times Sq/Theatre District", "dropoff_borough": "Manhattan", "passenger_count": 1, "trip_distance": 4.8, "fare_amount": 18.5, "total_amount": 24.3, "payment_type": 1, "congestion_surcharge": 2.5, "ratecodeid": 1.0},
        },
        {
            "time_object": {"timestamp": "2026-04-15 12:00:00.000000", "duration": 10.0, "duration_unit": "minute", "timezone": "America/New_York"},
            "event_type": "taxi_pickup",
            "attribute": {"vendorid": 1, "pickup_locationid": 237, "pickup_zone": "Upper East Side South", "pickup_borough": "Manhattan", "dropoff_locationid": 140, "dropoff_zone": "Lenox Hill East", "dropoff_borough": "Manhattan", "passenger_count": 3, "trip_distance": 1.2, "fare_amount": 8.0, "total_amount": 11.8, "payment_type": 2, "congestion_surcharge": 0, "ratecodeid": 1.0},
        },
        {
            "time_object": {"timestamp": "2026-04-16 09:30:00.000000", "duration": 15.0, "duration_unit": "minute", "timezone": "America/New_York"},
            "event_type": "taxi_pickup",
            "attribute": {"vendorid": 2, "pickup_locationid": 100, "pickup_zone": "Garment District", "pickup_borough": "Manhattan", "dropoff_locationid": 200, "dropoff_zone": "Riverdale/North Riverdale/Fieldston", "dropoff_borough": "Bronx", "passenger_count": 2, "trip_distance": 3.0, "fare_amount": 12.0, "total_amount": 16.0, "payment_type": 1, "congestion_surcharge": 2.5, "ratecodeid": 1.0},
        },
    ],
}

MOCK_WEATHER_ADAGE = {
    "data_source": "open_meteo",
    "dataset_type": "weather_forecast",
    "dataset_id": "s3://bucket/weather/raw/test.json",
    "time_object": {"timestamp": "2026-03-15 10:00:00.000000", "timezone": "America/New_York"},
    "events": [
        {
            "time_object": {"timestamp": "2026-04-15T08:00", "duration": 1, "duration_unit": "hour", "timezone": "America/New_York"},
            "event_type": "weather_forecast",
            "attribute": {"precipitation_mm": 0.0, "temperature_c": 15.0, "demand_modifier": 1.0, "weather_category": "clear"},
        },
        {
            "time_object": {"timestamp": "2026-04-15T14:00", "duration": 1, "duration_unit": "hour", "timezone": "America/New_York"},
            "event_type": "weather_forecast",
            "attribute": {"precipitation_mm": 3.5, "temperature_c": 12.0, "demand_modifier": 1.15, "weather_category": "light_rain"},
        },
        {
            "time_object": {"timestamp": "2026-04-16T10:00", "duration": 1, "duration_unit": "hour", "timezone": "America/New_York"},
            "event_type": "weather_forecast",
            "attribute": {"precipitation_mm": 0.0, "temperature_c": 20.0, "demand_modifier": 1.0, "weather_category": "clear"},
        },
    ],
}


# ── ADAGE Schema Validation ─────────────────────────────────────────────────

def test_validate_ticketmaster_adage():
    valid, msg = validate_adage3(MOCK_TICKETMASTER_ADAGE)
    assert valid, msg


def test_validate_taxi_adage():
    valid, msg = validate_adage3(MOCK_TAXI_ADAGE)
    assert valid, msg


def test_validate_weather_adage():
    valid, msg = validate_adage3(MOCK_WEATHER_ADAGE)
    assert valid, msg


def test_validate_rejects_missing_data_source():
    bad = {**MOCK_TICKETMASTER_ADAGE}
    del bad["data_source"]
    valid, msg = validate_adage3(bad)
    assert not valid
    assert "data_source" in msg


def test_validate_rejects_missing_event_type():
    bad_event = {
        "time_object": {"timestamp": "2026-01-01", "duration": 1, "duration_unit": "hour", "timezone": "UTC"},
        "attribute": {"a": 1},
    }
    bad = {**MOCK_TICKETMASTER_ADAGE, "events": [bad_event]}
    valid, msg = validate_adage3(bad)
    assert not valid


def test_validate_rejects_empty_events():
    bad = {**MOCK_TICKETMASTER_ADAGE, "events": []}
    valid, msg = validate_adage3(bad)
    assert not valid


# ── Normaliser: Ticketmaster ─────────────────────────────────────────────────

def test_normalise_ticketmaster_groups_by_date():
    result = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    assert len(result) == 2
    assert result[0]["date"] == "2026-04-15"
    assert result[1]["date"] == "2026-04-16"


def test_normalise_ticketmaster_event_count():
    result = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    assert result[0]["event_count"] == 2
    assert result[1]["event_count"] == 1


def test_normalise_ticketmaster_event_names():
    result = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    assert "Rock Concert" in result[0]["event_names"]
    assert "Knicks Game" in result[0]["event_names"]


def test_normalise_ticketmaster_source_field():
    result = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    for r in result:
        assert r["source"] == "ticketmaster"


def test_normalise_ticketmaster_empty():
    empty = {**MOCK_TICKETMASTER_ADAGE, "events": []}
    result = normalise_ticketmaster(empty)
    assert result == []


# ── Normaliser: NYC Taxi ─────────────────────────────────────────────────────

def test_normalise_taxi_groups_by_date():
    result = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    assert len(result) == 2
    assert result[0]["date"] == "2026-04-15"
    assert result[1]["date"] == "2026-04-16"


def test_normalise_taxi_trip_count():
    result = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    assert result[0]["trip_count"] == 2
    assert result[1]["trip_count"] == 1


def test_normalise_taxi_avg_distance():
    result = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    assert result[0]["avg_trip_distance_miles"] == 3.0  # (4.8 + 1.2) / 2


def test_normalise_taxi_avg_fare():
    result = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    assert result[0]["avg_fare_amount"] == 13.25  # (18.5 + 8.0) / 2


def test_normalise_taxi_avg_duration():
    result = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    assert result[0]["avg_trip_duration_min"] == 16.75  # (23.5 + 10.0) / 2


def test_normalise_taxi_total_passengers():
    result = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    assert result[0]["total_passengers"] == 4  # 1 + 3


def test_normalise_taxi_top_borough():
    result = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    assert result[0]["top_borough"] == "Manhattan"


def test_normalise_taxi_empty():
    empty = {**MOCK_TAXI_ADAGE, "events": []}
    result = normalise_nyc_taxi(empty)
    assert result == []


# ── Normaliser: Weather ──────────────────────────────────────────────────────

def test_normalise_weather_groups_by_date():
    result = normalise_weather(MOCK_WEATHER_ADAGE)
    assert len(result) == 2
    assert result[0]["date"] == "2026-04-15"


def test_normalise_weather_temperature():
    result = normalise_weather(MOCK_WEATHER_ADAGE)
    apr15 = result[0]
    assert apr15["temperature_max_c"] == 15.0
    assert apr15["temperature_min_c"] == 12.0
    assert apr15["temperature_avg_c"] == 13.5  # (15 + 12) / 2


def test_normalise_weather_precipitation():
    result = normalise_weather(MOCK_WEATHER_ADAGE)
    assert result[0]["precipitation_total_mm"] == 3.5
    assert result[1]["precipitation_total_mm"] == 0.0


def test_normalise_weather_dominant_condition():
    result = normalise_weather(MOCK_WEATHER_ADAGE)
    assert result[1]["dominant_weather"] == "clear"


def test_normalise_weather_avg_demand_modifier():
    result = normalise_weather(MOCK_WEATHER_ADAGE)
    assert result[0]["avg_demand_modifier"] == 1.07  # (1.0 + 1.15) / 2 = 1.075 -> 1.07 (banker's rounding)


def test_normalise_weather_empty():
    empty = {**MOCK_WEATHER_ADAGE, "events": []}
    result = normalise_weather(empty)
    assert result == []


# ── Merger ───────────────────────────────────────────────────────────────────

def test_merge_combines_all_sources():
    tm = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    taxi = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    weather = normalise_weather(MOCK_WEATHER_ADAGE)
    merged = merge_by_date(tm, taxi, weather)
    assert len(merged) == 2


def test_merge_has_all_fields():
    tm = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    taxi = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    weather = normalise_weather(MOCK_WEATHER_ADAGE)
    merged = merge_by_date(tm, taxi, weather)

    record = merged[0]
    assert "date" in record
    assert "location" in record
    assert "event_count" in record
    assert "trip_count" in record
    assert "temperature_max_c" in record
    assert "precipitation_total_mm" in record
    assert "dominant_weather" in record
    assert "sources_present" in record
    assert "top_borough" in record


def test_merge_correct_values_apr15():
    tm = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    taxi = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    weather = normalise_weather(MOCK_WEATHER_ADAGE)
    merged = merge_by_date(tm, taxi, weather)

    apr15 = merged[0]
    assert apr15["date"] == "2026-04-15"
    assert apr15["event_count"] == 2
    assert apr15["trip_count"] == 2
    assert apr15["temperature_max_c"] == 15.0
    assert apr15["precipitation_total_mm"] == 3.5


def test_merge_sources_present():
    tm = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    taxi = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    weather = normalise_weather(MOCK_WEATHER_ADAGE)
    merged = merge_by_date(tm, taxi, weather)

    assert "ticketmaster" in merged[0]["sources_present"]
    assert "nyc_tlc" in merged[0]["sources_present"]
    assert "open_meteo" in merged[0]["sources_present"]


def test_merge_sorted_by_date():
    tm = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    taxi = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    weather = normalise_weather(MOCK_WEATHER_ADAGE)
    merged = merge_by_date(tm, taxi, weather)

    dates = [r["date"] for r in merged]
    assert dates == sorted(dates)


def test_merge_with_missing_source():
    tm = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    merged = merge_by_date(tm, [], [])
    assert len(merged) == 2
    assert merged[0]["trip_count"] == 0
    assert merged[0]["top_borough"] == "Unknown"
    assert merged[0]["temperature_max_c"] == 0
    assert merged[0]["sources_present"] == ["ticketmaster"]


def test_merge_empty_all_sources():
    merged = merge_by_date([], [], [])
    assert merged == []


def test_merge_location_default():
    tm = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    merged = merge_by_date(tm, [], [])
    assert merged[0]["location"]["city"] == "New York"
    assert merged[0]["location"]["lat"] == 40.7128


# ── Merged to ADAGE ─────────────────────────────────────────────────────────

def test_merged_to_adage_structure():
    tm = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    taxi = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    weather = normalise_weather(MOCK_WEATHER_ADAGE)
    merged = merge_by_date(tm, taxi, weather)
    adage = merged_to_adage(merged)

    assert adage["data_source"] == "merged"
    assert adage["dataset_type"] == "demand_features"
    assert len(adage["events"]) == 2


def test_merged_to_adage_validates():
    tm = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    taxi = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    weather = normalise_weather(MOCK_WEATHER_ADAGE)
    merged = merge_by_date(tm, taxi, weather)
    adage = merged_to_adage(merged)

    valid, msg = validate_adage3(adage)
    assert valid, msg


def test_merged_to_adage_event_attributes():
    tm = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    taxi = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    weather = normalise_weather(MOCK_WEATHER_ADAGE)
    merged = merge_by_date(tm, taxi, weather)
    adage = merged_to_adage(merged)

    attr = adage["events"][0]["attribute"]
    assert attr["event_count"] == 2
    assert attr["trip_count"] == 2
    assert attr["temperature_max_c"] == 15.0
    assert attr["city"] == "New York"


def test_merged_to_adage_time_object():
    tm = normalise_ticketmaster(MOCK_TICKETMASTER_ADAGE)
    taxi = normalise_nyc_taxi(MOCK_TAXI_ADAGE)
    weather = normalise_weather(MOCK_WEATHER_ADAGE)
    merged = merge_by_date(tm, taxi, weather)
    adage = merged_to_adage(merged)

    event_time = adage["events"][0]["time_object"]
    assert event_time["duration"] == 24
    assert event_time["duration_unit"] == "hour"
    assert "2026-04-15" in event_time["timestamp"]
