"""Merge normalised daily records from all three sources by date.

Takes the output of normaliser.normalise_ticketmaster(), normalise_nyc_taxi(),
and normalise_weather() and produces one merged record per day.
"""

from datetime import datetime, timezone


def merge_by_date(
    ticketmaster_daily: list[dict],
    taxi_daily: list[dict],
    weather_daily: list[dict],
    city: str = "New York",
    lat: float = 40.7128,
    lng: float = -74.0060,
) -> list[dict]:
    """Merge normalised records from all three sources into one record per day.

    Returns a sorted list of merged daily records.
    """
    all_dates: set[str] = set()
    tm_by_date = _index_by_date(ticketmaster_daily)
    taxi_by_date = _index_by_date(taxi_daily)
    weather_by_date = _index_by_date(weather_daily)

    all_dates.update(tm_by_date.keys(), taxi_by_date.keys(), weather_by_date.keys())

    merged = []
    for date_str in sorted(all_dates):
        tm = tm_by_date.get(date_str, {})
        taxi = taxi_by_date.get(date_str, {})
        weather = weather_by_date.get(date_str, {})

        record = {
            "date": date_str,
            "location": {"lat": lat, "lng": lng, "city": city},
            "event_count": tm.get("event_count", 0),
            "total_expected_attendance": tm.get("total_expected_attendance", 0),
            "event_names": tm.get("event_names", []),
            "trip_count": taxi.get("trip_count", 0),
            "avg_trip_distance_miles": taxi.get("avg_trip_distance_miles", 0),
            "avg_fare_amount": taxi.get("avg_fare_amount", 0),
            "avg_trip_duration_min": taxi.get("avg_trip_duration_min", 0),
            "total_passengers": taxi.get("total_passengers", 0),
            "top_borough": taxi.get("top_borough", "Unknown"),
            "temperature_max_c": weather.get("temperature_max_c", 0),
            "temperature_min_c": weather.get("temperature_min_c", 0),
            "temperature_avg_c": weather.get("temperature_avg_c", 0),
            "precipitation_total_mm": weather.get("precipitation_total_mm", 0),
            "avg_demand_modifier": weather.get("avg_demand_modifier", 1.0),
            "dominant_weather": weather.get("dominant_weather", "unknown"),
            "sources_present": _sources_present(tm, taxi, weather),
        }
        merged.append(record)

    return merged


def merged_to_adage(
    merged_records: list[dict],
    bucket: str = "bucket-placeholder",
) -> dict:
    """Convert merged daily records back into ADAGE 3.0 format for storage."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
    date_range = ""
    if merged_records:
        date_range = f"{merged_records[0]['date']}_to_{merged_records[-1]['date']}"

    adage_output = {
        "data_source": "merged",
        "dataset_type": "demand_features",
        "dataset_id": f"s3://{bucket}/processed/merged/{date_range}",
        "time_object": {
            "timestamp": now,
            "timezone": "America/New_York",
        },
        "events": [],
    }

    for record in merged_records:
        location = record.get("location", {})
        event = {
            "time_object": {
                "timestamp": f"{record['date']} 00:00:00.000000",
                "duration": 24,
                "duration_unit": "hour",
                "timezone": "America/New_York",
            },
            "event_type": "daily_demand_features",
            "attribute": {
                "date": record["date"],
                "city": location.get("city", ""),
                "latitude": location.get("lat"),
                "longitude": location.get("lng"),
                "event_count": record["event_count"],
                "total_expected_attendance": record["total_expected_attendance"],
                "event_names": record["event_names"],
                "trip_count": record["trip_count"],
                "avg_trip_distance_miles": record["avg_trip_distance_miles"],
                "avg_fare_amount": record["avg_fare_amount"],
                "avg_trip_duration_min": record["avg_trip_duration_min"],
                "total_passengers": record["total_passengers"],
                "top_borough": record["top_borough"],
                "temperature_max_c": record["temperature_max_c"],
                "temperature_min_c": record["temperature_min_c"],
                "temperature_avg_c": record["temperature_avg_c"],
                "precipitation_total_mm": record["precipitation_total_mm"],
                "avg_demand_modifier": record["avg_demand_modifier"],
                "dominant_weather": record["dominant_weather"],
                "sources_present": record["sources_present"],
            },
        }
        adage_output["events"].append(event)

    return adage_output


def _index_by_date(records: list[dict]) -> dict[str, dict]:
    """Create a lookup dict from date string to record."""
    return {r["date"]: r for r in records if "date" in r}


def _sources_present(tm: dict, taxi: dict, weather: dict) -> list[str]:
    """List which data sources contributed to this day's record."""
    sources = []
    if tm:
        sources.append("ticketmaster")
    if taxi:
        sources.append("nyc_tlc")
    if weather:
        sources.append("open_meteo")
    return sources
