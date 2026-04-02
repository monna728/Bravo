import json
import os
import sys
import time
import boto3
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.lambda_observability import deployment_env, emit_embedded_metric, log_event
from taxiZone_lookup import ZONE_LOOKUP

NYC_TLC_API = "https://data.cityofnewyork.us/resource/4b4i-vvec.json"
S3_BUCKET   = "rushhour-data"
S3_KEY = f"tlc/raw/tlc_trips_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
# S3_KEY      = "tlc/raw/tlc_trips.json"
LIMIT       = 1000
TIMEZONE    = "America/New_York"

def fetch_tlc_data(limit=LIMIT):
    params = {"$limit": limit, "$order": "tpep_pickup_datetime DESC"}
    response = requests.get(NYC_TLC_API, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def calculate_duration_minutes(pickup_str, dropoff_str):
    fmt = "%Y-%m-%dT%H:%M:%S.%f"
    try:
        pickup  = datetime.strptime(pickup_str, fmt)
        dropoff = datetime.strptime(dropoff_str, fmt)
        return round((dropoff - pickup).total_seconds() / 60, 2)
    except Exception:
        return 0
    
def locationid_to_zone(location_id: int):
    return ZONE_LOOKUP.get(location_id, ("Unknown", "Unknown"))

# convert raw NYC TLC records into the ADAGE 3.0 data model format and each taxi trip becomes one 'event' in the events array
def transform_to_adage(raw_records):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    adage_output = {
        "data_source": "nyc_tlc",
        "dataset_type": "taxi_trips",
        "dataset_id": f"s3://{S3_BUCKET}/{S3_KEY}",
        "time_object": {
            "timestamp": now,
            "timezone": TIMEZONE
        },
        "events": []
    }

    for record in raw_records:
        pickup_time  = record.get("tpep_pickup_datetime", "")
        dropoff_time = record.get("tpep_dropoff_datetime", "")
        duration_min = calculate_duration_minutes(pickup_time, dropoff_time)
        pickup_formatted = pickup_time.replace("T", " ").replace(".000", ".000000")

        pu_id = int(record.get("pulocationid",0))
        do_id = int(record.get("dolocationid",0))

        pu_borough, pu_zone = locationid_to_zone(pu_id)
        do_borough, do_zone = locationid_to_zone(do_id)

        event = {
            "time_object": {
                "timestamp":     pickup_formatted,
                "duration":      duration_min,
                "duration_unit": "minute",
                "timezone":      TIMEZONE
            },
            "event_type": "taxi_pickup",
            "attribute": {
                "vendorid":           int(record.get("vendorid", 0)),
                "pickup_locationid":  pu_id,
                "pickup_zone":        pu_zone,
                "pickup_borough":     pu_borough,
                "dropoff_locationid": do_id,
                "dropoff_zone":       do_zone,
                "dropoff_borough":    do_borough,
                "passenger_count":    float(record.get("passenger_count", 0)),
                "trip_distance":      float(record.get("trip_distance", 0)),
                "fare_amount":        float(record.get("fare_amount", 0)),
                "total_amount":       float(record.get("total_amount", 0)),
                "payment_type":       int(record.get("payment_type", 0)),
                "congestion_surcharge": float(record.get("congestion_surcharge", 0)),
                "ratecodeid":         float(record.get("ratecodeid", 1))
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
    log_event("collect-nyc-tlc", "collection started", context=context, event=ev)

    raw_records = fetch_tlc_data(limit=LIMIT)
    print(f"Fetched {len(raw_records)} records from NYC TLC API")

    adage_data = transform_to_adage(raw_records)
    print(f"Transformed {len(adage_data['events'])} events into ADAGE format")

    try:
        print(f"Attempting to save {len(adage_data['events'])} events to s3://{S3_BUCKET}/{S3_KEY}")
        save_to_s3(adage_data, S3_BUCKET, S3_KEY)
    except Exception as e:
        log_event(
            "collect-nyc-tlc", "s3 save failed", level="ERROR", context=context, event=ev,
            duration_ms=(time.perf_counter() - t0) * 1000, error_type=type(e).__name__,
        )
        print("Failed to save to S3:", e)
        raise

    n = len(adage_data["events"])
    elapsed_ms = (time.perf_counter() - t0) * 1000
    log_event(
        "collect-nyc-tlc", "collection complete", context=context, event=ev,
        duration_ms=elapsed_ms, records_collected=n, s3_key=S3_KEY,
    )
    emit_embedded_metric(
        "Bravo",
        {"RecordsCollected": float(n)},
        {"Service": "collect-nyc-tlc", "Environment": deployment_env()},
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Data collection complete",
            "records_collected": n,
            "s3_location": f"s3://{S3_BUCKET}/{S3_KEY}"
        })
    }


if __name__ == "__main__":
    print("Running local test (simulating Lambda)...")

    response = lambda_handler(event={}, context=None)

    print("Lambda response:")
    print(json.dumps(response, indent=2))