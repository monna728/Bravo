import json
import boto3
import requests
from datetime import datetime, timezone

OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"
S3_BUCKET      = "S3_BUCKET"
# S3_KEY = f"weather/raw/weather_forecast_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
S3_KEY         = "weather/raw/weather_forecast.json"
# NYC coordinates (Midtown Manhattan)
DEFAULT_LAT    = 40.7128
DEFAULT_LNG    = -74.0060
TIMEZONE       = "America/New_York"
FORECAST_DAYS  = 7


# call the Open-Meteo API and return raw forecast response
def fetch_weather_data(lat=DEFAULT_LAT, lng=DEFAULT_LNG, forecast_days=FORECAST_DAYS):
    params = {
        "latitude":              lat,
        "longitude":             lng,
        "hourly":                "precipitation,temperature_2m,precipitation_probability",
        "forecast_days":         forecast_days,
        "timezone":              TIMEZONE,
    }
    response = requests.get(OPEN_METEO_API, params=params, timeout=30)
    # checks the HTTP status code and raises an exception if the request was unsuccessful
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
        precipitation_mm = float(precip[i])   if i < len(precip)      else 0.0
        temperature_c    = float(temp[i])      if i < len(temp)        else 0.0
        precip_pct       = int(precip_prob[i]) if i < len(precip_prob) else 0

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
    print("Starting weather data collection...")

    lat = event.get("lat", DEFAULT_LAT)
    lng = event.get("lng", DEFAULT_LNG)

    raw_response = fetch_weather_data(lat=lat, lng=lng)
    print(f"Fetched {len(raw_response.get('hourly', {}).get('time', []))} hourly records from Open-Meteo")

    adage_data = transform_to_adage(raw_response, lat=lat, lng=lng)
    print(f"Transformed {len(adage_data['events'])} events into ADAGE format")

    save_to_s3(adage_data, S3_BUCKET, S3_KEY)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message":           "Weather data collection complete",
            "records_collected": len(adage_data["events"]),
            "s3_location":       f"s3://{S3_BUCKET}/{S3_KEY}"
        })
    }


if __name__ == "__main__":
    print("Running local test (simulating Lambda)...")

    response = lambda_handler(event={}, context=None)

    print("Lambda response:")
    print(json.dumps(response, indent=2))