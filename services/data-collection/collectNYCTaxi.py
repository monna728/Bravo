import json
import boto3
import requests
from datetime import datetime, timezone
from taxiZone_lookup import ZONE_LOOKUP

NYC_TLC_API = "https://data.cityofnewyork.us/resource/4b4i-vvec.json"
# replace with bucket from AWS
S3_BUCKET   = "bucket-placeholder"
# replace with path inside bucket
S3_KEY      = "tlc/raw/tlc_trips.json"
# 1000 for now
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

        pu_zone, pu_borough = locationid_to_zone(pu_id)
        do_zone, do_borough = locationid_to_zone(do_id)

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

# AWS Lambda entry point
# called automatically by AWS when triggered
def lambda_handler(event, context):
    print("Starting TLC data collection...")

    raw_records = fetch_tlc_data(limit=LIMIT)
    print(f"Fetched {len(raw_records)} records from NYC TLC API")

    adage_data = transform_to_adage(raw_records)
    print(f"Transformed {len(adage_data['events'])} events into ADAGE format")

    save_to_s3(adage_data, S3_BUCKET, S3_KEY)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Data collection complete",
            "records_collected": len(adage_data["events"]),
            "s3_location": f"s3://{S3_BUCKET}/{S3_KEY}"
        })
    }


# locally testing before using AWS S3 bucket
if __name__ == "__main__":
    import json

    raw_records = fetch_tlc_data(limit=50)
    print(f"Fetched {len(raw_records)} records")

    adage_data = transform_to_adage(raw_records)
    print(f"Transformed {len(adage_data['events'])} events")

    # creating test output file for local testing
    with open("test_output.json", "w") as f:
        json.dump(adage_data, f, indent=2)
    print("Output saved to test_output.json")