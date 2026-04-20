import json
import os
import sys
import time
import boto3
import requests
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.cors import CORS_HEADERS
from shared.lambda_observability import deployment_env, emit_embedded_metric, log_event

OPEN_METEO_FORECAST_API = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_ARCHIVE_API = "https://archive-api.open-meteo.com/v1/archive"
S3_BUCKET      = "rushhour-data"
# S3_KEY = f"weather/raw/weather_forecast_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
S3_KEY         = "weather/raw/weather_forecast.json"
# NYC coordinates (Midtown Manhattan)
DEFAULT_LAT    = 40.7128
DEFAULT_LNG    = -74.0060
TIMEZONE       = "America/New_York"
FORECAST_DAYS  = 7
WEATHER_LOOKBACK_DAYS = 90

# Partner integration — T18_ECHO (Venus) Sydney coordinates
SYDNEY_LAT     = -33.8688
SYDNEY_LNG     = 151.2093
# Stable S3 key for the daily-refreshed Sydney raw forecast (raw Open-Meteo JSON, no ADAGE wrapping).
# T18_ECHO reads this key directly via GET /retrieve?source=sydney_forecast.
SYDNEY_RAW_S3_KEY = "weather/raw/sydney_forecast.json"


def fetch_weather_data(
    lat=DEFAULT_LAT,
    lng=DEFAULT_LNG,
    *,
    forecast_days: int | None = None,
    lookback_days: int = WEATHER_LOOKBACK_DAYS,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Return Open-Meteo hourly JSON.

    If ``forecast_days`` is set, uses the short-range **forecast** API (for tests / quick runs).
    Otherwise uses the **archive** API for ``lookback_days`` ending ``end_date`` (default: today),
    giving roughly that many calendar days of hourly history (>= 90 days when defaults apply).

    Timezone: "auto" is used for non-NYC coordinates so Open-Meteo returns
    timestamps in the correct local time for that location (e.g. AEST for Sydney).
    """
    tz = TIMEZONE if (lat == DEFAULT_LAT and lng == DEFAULT_LNG) else "auto"

    if forecast_days is not None:
        params = {
            "latitude": lat,
            "longitude": lng,
            "hourly": "precipitation,temperature_2m,precipitation_probability",
            "forecast_days": forecast_days,
            "timezone": tz,
        }
        response = requests.get(OPEN_METEO_FORECAST_API, params=params, timeout=60)
        response.raise_for_status()
        return response.json()

    end = end_date or date.today().isoformat()
    if start_date:
        start = start_date
    else:
        end_d = date.fromisoformat(end)
        start = (end_d - timedelta(days=lookback_days - 1)).isoformat()

    params = {
        "latitude": lat,
        "longitude": lng,
        "start_date": start,
        "end_date": end,
        "hourly": "precipitation,temperature_2m,precipitation_probability",
        "timezone": tz,
    }
    response = requests.get(OPEN_METEO_ARCHIVE_API, params=params, timeout=120)
    response.raise_for_status()
    return response.json()


# compute a demand modifier multiplier from precipitation and temperature
# based on empirical ride-sharing demand patterns:
#   heavy rain (>=5mm/hr): +30% demand
#   light rain (1-5mm/hr): +15% demand
#   drizzle (0-1mm/hr):    +5% demand
#   very cold (<5 C):      +10% demand
#   very hot (>35 C):      +5% demand
def compute_demand_modifier(precipitation_mm, temperature_c):
    modifier = 1.0
    if precipitation_mm >= 5.0:
        modifier += 0.30
    elif precipitation_mm >= 1.0:
        modifier += 0.15
    elif precipitation_mm > 0:
        modifier += 0.05
    if temperature_c < 5.0:
        modifier += 0.10
    elif temperature_c > 35.0:
        modifier += 0.05
    return round(modifier, 2)


# classify precipitation into a human-readable weather category
def classify_weather(precipitation_mm):
    if precipitation_mm == 0:
        return "clear"
    elif precipitation_mm < 1.0:
        return "drizzle"
    elif precipitation_mm < 5.0:
        return "light_rain"
    elif precipitation_mm < 10.0:
        return "heavy_rain"
    return "extreme"


def _safe_float(value, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# convert raw Open-Meteo response into ADAGE 3.0 data model format
# each hourly forecast slot becomes one 'event' in the events array
def transform_to_adage(raw_response, lat=DEFAULT_LAT, lng=DEFAULT_LNG):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    hourly     = raw_response.get("hourly", {})
    times      = hourly.get("time", [])
    precip     = hourly.get("precipitation", [])
    temp       = hourly.get("temperature_2m", [])
    precip_prob = hourly.get("precipitation_probability", [])

    adage_output = {
        "data_source":   "open_meteo",
        "dataset_type":  "weather_forecast",
        "dataset_id":    f"s3://{S3_BUCKET}/{S3_KEY}",
        "time_object": {
            "timestamp": now,
            "timezone":  TIMEZONE
        },
        "events": []
    }

    for i, timestamp in enumerate(times):
        precipitation_mm = _safe_float(precip[i]) if i < len(precip) else 0.0
        temperature_c = _safe_float(temp[i]) if i < len(temp) else 0.0
        precip_pct = _safe_int(precip_prob[i]) if i < len(precip_prob) else 0

        event = {
            "time_object": {
                "timestamp":     timestamp,
                "duration":      1,
                "duration_unit": "hour",
                "timezone":      TIMEZONE
            },
            "event_type": "weather_forecast",
            "attribute": {
                "latitude":                  lat,
                "longitude":                 lng,
                "precipitation_mm":          precipitation_mm,
                "temperature_c":             temperature_c,
                "precipitation_probability": precip_pct,
                "demand_modifier":           compute_demand_modifier(precipitation_mm, temperature_c),
                "weather_category":          classify_weather(precipitation_mm),
            }
        }
        adage_output["events"].append(event)

    return adage_output


def save_to_s3(data: dict, bucket: str, key: str):
    # save a Python dict as a JSON file to S3 bucket
    s3_client = boto3.client("s3")
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data, indent=2),
        ContentType="application/json"
    )
    print(f"Saved to s3://{bucket}/{key}")


def lambda_handler(event, context):
    t0 = time.perf_counter()
    ev = event if isinstance(event, dict) else {}
    log_event("collect-weather", "collection started", context=context, event=ev)

    lat = ev.get("lat", DEFAULT_LAT)
    lng = ev.get("lng", DEFAULT_LNG)
    lookback = int(ev.get("lookback_days", WEATHER_LOOKBACK_DAYS))
    start_d = ev.get("start_date")
    end_d = ev.get("end_date")
    use_forecast = ev.get("use_forecast_only") is True
    fd = FORECAST_DAYS if use_forecast else None
    # return_raw=True: skip ADAGE wrapping, save raw Open-Meteo JSON to a
    # location-specific key and return it directly.  Used by partner integrations
    # (e.g. T18_ECHO Venus) that consume the Open-Meteo schema directly.
    return_raw = ev.get("return_raw") is True

    raw_response = fetch_weather_data(
        lat=lat,
        lng=lng,
        forecast_days=fd,
        lookback_days=lookback,
        start_date=start_d,
        end_date=end_d,
    )
    n_hourly = len(raw_response.get("hourly", {}).get("time", []))
    print(f"Fetched {n_hourly} hourly records from Open-Meteo")

    try:
        if return_raw:
            # Stable per-location key so partners always GET the latest version.
            raw_key = ev.get("raw_s3_key", SYDNEY_RAW_S3_KEY)
            save_to_s3(raw_response, S3_BUCKET, raw_key)
            print(f"Saved raw Open-Meteo JSON to s3://{S3_BUCKET}/{raw_key}")
        else:
            adage_data = transform_to_adage(raw_response, lat=lat, lng=lng)
            print(f"Transformed {len(adage_data['events'])} events into ADAGE format")
            save_to_s3(adage_data, S3_BUCKET, S3_KEY)
    except Exception as e:
        log_event(
            "collect-weather", "s3 save failed", level="ERROR", context=context, event=ev,
            duration_ms=(time.perf_counter() - t0) * 1000, error_type=type(e).__name__,
        )
        raise

    n = n_hourly if return_raw else len(adage_data["events"])
    s3_saved = raw_key if return_raw else S3_KEY
    elapsed_ms = (time.perf_counter() - t0) * 1000
    log_event(
        "collect-weather", "collection complete", context=context, event=ev,
        duration_ms=elapsed_ms, records_collected=n, s3_key=s3_saved,
    )
    emit_embedded_metric(
        "Bravo",
        {"RecordsCollected": float(n)},
        {"Service": "collect-weather", "Environment": deployment_env()},
    )

    body: dict = {
        "message":           "Weather data collection complete",
        "records_collected": n,
        "s3_location":       f"s3://{S3_BUCKET}/{s3_saved}",
    }
    if return_raw:
        body["data"] = raw_response

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": json.dumps(body),
    }


if __name__ == "__main__":
    print("Running local test (simulating Lambda)...")

    response = lambda_handler(event={}, context=None)

    print("Lambda response:")
    print(json.dumps(response, indent=2))