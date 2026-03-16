"""Normalise raw ADAGE data from each source into flat daily records.

Each normalise function takes an ADAGE 3.0 dict (as produced by the collectors)
and returns a list of dicts, one per day, with standardised keys ready for merging.
"""

from datetime import datetime
from collections import defaultdict


def normalise_ticketmaster(adage_data: dict) -> list[dict]:
    """Normalise Ticketmaster ADAGE data into daily event summaries.

    Returns one record per day with event_count and total expected attendance.
    """
    daily: dict[str, dict] = defaultdict(lambda: {
        "event_count": 0,
        "total_expected_attendance": 0,
        "event_names": [],
    })

    for event in adage_data.get("events", []):
        timestamp = event.get("time_object", {}).get("timestamp", "")
        date_str = _extract_date(timestamp)
        if not date_str:
            continue

        attr = event.get("attribute", {})
        daily[date_str]["event_count"] += 1
        daily[date_str]["event_names"].append(attr.get("event_name", ""))

    result = []
    for date_str, info in sorted(daily.items()):
        result.append({
            "date": date_str,
            "source": "ticketmaster",
            "event_count": info["event_count"],
            "total_expected_attendance": info["total_expected_attendance"],
            "event_names": info["event_names"],
        })
    return result


def normalise_nyc_taxi(adage_data: dict) -> list[dict]:
    """Normalise NYC TLC ADAGE data into daily trip summaries.

    Returns one record per day with trip_count, avg distance, and avg fare.
    """
    daily: dict[str, dict] = defaultdict(lambda: {
        "trip_count": 0,
        "total_distance": 0.0,
        "total_fare": 0.0,
        "total_duration": 0.0,
        "total_passengers": 0,
        "boroughs": [],
    })

    for event in adage_data.get("events", []):
        timestamp = event.get("time_object", {}).get("timestamp", "")
        duration = event.get("time_object", {}).get("duration", 0)
        date_str = _extract_date(timestamp)
        if not date_str:
            continue

        attr = event.get("attribute", {})
        day = daily[date_str]
        day["trip_count"] += 1
        day["total_distance"] += float(attr.get("trip_distance", 0))
        day["total_fare"] += float(attr.get("fare_amount", 0))
        day["total_duration"] += float(duration)
        day["total_passengers"] += int(float(attr.get("passenger_count", 0)))
        pickup_borough = attr.get("pickup_borough", "")
        if pickup_borough and pickup_borough != "Unknown":
            day["boroughs"].append(pickup_borough)

    result = []
    for date_str, info in sorted(daily.items()):
        count = info["trip_count"]
        result.append({
            "date": date_str,
            "source": "nyc_tlc",
            "trip_count": count,
            "avg_trip_distance_miles": round(info["total_distance"] / count, 2) if count else 0,
            "avg_fare_amount": round(info["total_fare"] / count, 2) if count else 0,
            "avg_trip_duration_min": round(info["total_duration"] / count, 2) if count else 0,
            "total_passengers": info["total_passengers"],
            "top_borough": _most_common(info["boroughs"]) if info["boroughs"] else "Unknown",
        })
    return result


def normalise_weather(adage_data: dict) -> list[dict]:
    """Normalise Open-Meteo ADAGE data into daily weather summaries.

    Aggregates hourly readings into daily max temp, total precipitation, etc.
    """
    daily: dict[str, dict] = defaultdict(lambda: {
        "temps": [],
        "precip_total": 0.0,
        "demand_modifiers": [],
        "categories": [],
    })

    for event in adage_data.get("events", []):
        timestamp = event.get("time_object", {}).get("timestamp", "")
        date_str = _extract_date(timestamp)
        if not date_str:
            continue

        attr = event.get("attribute", {})
        day = daily[date_str]
        day["temps"].append(float(attr.get("temperature_c", 0)))
        day["precip_total"] += float(attr.get("precipitation_mm", 0))
        day["demand_modifiers"].append(float(attr.get("demand_modifier", 1.0)))
        category = attr.get("weather_category", "unknown")
        day["categories"].append(category)

    result = []
    for date_str, info in sorted(daily.items()):
        temps = info["temps"]
        result.append({
            "date": date_str,
            "source": "open_meteo",
            "temperature_max_c": round(max(temps), 1) if temps else 0,
            "temperature_min_c": round(min(temps), 1) if temps else 0,
            "temperature_avg_c": round(sum(temps) / len(temps), 1) if temps else 0,
            "precipitation_total_mm": round(info["precip_total"], 2),
            "avg_demand_modifier": round(
                sum(info["demand_modifiers"]) / len(info["demand_modifiers"]), 2
            ) if info["demand_modifiers"] else 1.0,
            "dominant_weather": _most_common(info["categories"]),
        })
    return result


def _extract_date(timestamp: str) -> str:
    """Extract YYYY-MM-DD from various timestamp formats."""
    if not timestamp:
        return ""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M",
                "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
        try:
            return datetime.strptime(timestamp, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return timestamp[:10] if len(timestamp) >= 10 else ""


def _most_common(items: list[str]) -> str:
    """Return the most frequently occurring item in a list."""
    if not items:
        return "unknown"
    counts: dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return max(counts, key=counts.get)
