import json
import os
import sys
import time
import boto3
import requests
from datetime import datetime, date, timedelta, timezone

try:
    from dotenv import load_dotenv
    _REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    load_dotenv(os.path.join(_REPO_ROOT, ".env"))
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.cors import CORS_HEADERS
from shared.lambda_observability import deployment_env, emit_embedded_metric, log_event
from taxiZone_lookup import ZONE_LOOKUP

NYC_TLC_API = "https://data.cityofnewyork.us/resource/4b4i-vvec.json"
S3_BUCKET   = "rushhour-data"
S3_KEY = f"tlc/raw/tlc_trips_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
TIMEZONE    = "America/New_York"

# --- Strategy: day-chunked sampling -------------------------------------------
# NYC taxis make ~600,000+ trips/day. A bulk paginated pull hits the row cap
# within a single day, so you end up with 1-3 distinct dates no matter how many
# pages you fetch.  Instead we sample TRIPS_PER_DAY trips for each calendar day
# across COLLECTION_LOOKBACK_DAYS days.  This guarantees 90 distinct dates and
# keeps the total file small (~45,000 rows at defaults — very manageable).
COLLECTION_LOOKBACK_DAYS = int(os.environ.get("NYC_TLC_LOOKBACK_DAYS", "90"))
TRIPS_PER_DAY = int(os.environ.get("NYC_TLC_TRIPS_PER_DAY", "500"))
TLC_REQUEST_TIMEOUT = (
    float(os.environ.get("NYC_TLC_CONNECT_TIMEOUT", "20")),
    float(os.environ.get("NYC_TLC_READ_TIMEOUT", "120")),
)
TLC_HTTP_RETRIES = int(os.environ.get("NYC_TLC_HTTP_RETRIES", "3"))
# ------------------------------------------------------------------------------


def _latest_dataset_date() -> date:
    """Return the most recent pickup date in the Socrata dataset (one-row probe)."""
    headers = {}
    app_token = os.environ.get("NYC_OPENDATA_APP_TOKEN", "").strip()
    if app_token:
        headers["X-App-Token"] = app_token
    params = {"$limit": 1, "$order": "tpep_pickup_datetime DESC"}
    resp = requests.get(NYC_TLC_API, params=params, headers=headers or None,
                        timeout=TLC_REQUEST_TIMEOUT)
    resp.raise_for_status()
    rows = resp.json()
    if not rows:
        return date.today()
    raw = rows[0].get("tpep_pickup_datetime", "")
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return date.today()


def fetch_tlc_data_for_day(target_date: date, limit: int = TRIPS_PER_DAY) -> list:
    """Fetch up to ``limit`` trips whose pickup date equals ``target_date``."""
    headers = {}
    app_token = os.environ.get("NYC_OPENDATA_APP_TOKEN", "").strip()
    if app_token:
        headers["X-App-Token"] = app_token

    day_start = f"{target_date}T00:00:00.000"
    day_end   = f"{target_date}T23:59:59.999"
    params = {
        "$limit":  limit,
        "$where":  f"tpep_pickup_datetime >= '{day_start}' AND tpep_pickup_datetime <= '{day_end}'",
        "$order":  "tpep_pickup_datetime ASC",
    }

    last_err: BaseException | None = None
    for attempt in range(max(1, TLC_HTTP_RETRIES)):
        try:
            resp = requests.get(NYC_TLC_API, params=params,
                                headers=headers or None,
                                timeout=TLC_REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            last_err = exc
            if attempt + 1 >= TLC_HTTP_RETRIES:
                raise
            time.sleep(2.0 * (attempt + 1))
    assert last_err is not None
    raise last_err


def fetch_tlc_trips_lookback(lookback_days: int = COLLECTION_LOOKBACK_DAYS,
                              trips_per_day: int = TRIPS_PER_DAY) -> list:
    """Sample ``trips_per_day`` trips per calendar day for ``lookback_days`` days.

    Anchors the window to the **newest date in the Socrata dataset** (probe query)
    so a PC clock ahead of publication does not create an empty date range.
    Returns a flat list of raw TLC row dicts.
    """
    end_date = _latest_dataset_date()
    all_rows: list = []
    skipped = 0

    for offset in range(lookback_days - 1, -1, -1):           # oldest → newest
        target = end_date - timedelta(days=offset)
        try:
            rows = fetch_tlc_data_for_day(target, limit=trips_per_day)
            all_rows.extend(rows)
            print(f"  {target}  {len(rows):>5} trips")
        except Exception as exc:
            skipped += 1
            print(f"  {target}  SKIP ({exc})")

    print(f"Day-chunked fetch: {len(all_rows)} total rows, {skipped} days skipped")
    return all_rows


# keep a single-day helper importable for tests / targeted backfills
fetch_tlc_data = fetch_tlc_data_for_day


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


def transform_to_adage(raw_records):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    adage_output = {
        "data_source": "nyc_tlc",
        "dataset_type": "taxi_trips",
        "dataset_id": f"s3://{S3_BUCKET}/{S3_KEY}",
        "time_object": {"timestamp": now, "timezone": TIMEZONE},
        "events": [],
    }
    for record in raw_records:
        pickup_time  = record.get("tpep_pickup_datetime", "")
        dropoff_time = record.get("tpep_dropoff_datetime", "")
        duration_min = calculate_duration_minutes(pickup_time, dropoff_time)
        pickup_formatted = pickup_time.replace("T", " ").replace(".000", ".000000")

        pu_id = int(record.get("pulocationid", 0))
        do_id = int(record.get("dolocationid", 0))
        pu_borough, pu_zone = locationid_to_zone(pu_id)
        do_borough, do_zone = locationid_to_zone(do_id)

        event = {
            "time_object": {
                "timestamp":     pickup_formatted,
                "duration":      duration_min,
                "duration_unit": "minute",
                "timezone":      TIMEZONE,
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
                "ratecodeid":         float(record.get("ratecodeid", 1)),
            },
        }
        adage_output["events"].append(event)
    return adage_output


def save_to_s3(data: dict, bucket: str, key: str):
    s3_client = boto3.client("s3")
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data, indent=2),
        ContentType="application/json",
    )
    print(f"Saved to s3://{bucket}/{key}")


def lambda_handler(event, context):
    t0 = time.perf_counter()
    ev = event if isinstance(event, dict) else {}
    log_event("collect-nyc-tlc", "collection started", context=context, event=ev)

    lookback     = int(ev.get("lookback_days", COLLECTION_LOOKBACK_DAYS))
    trips_per_day = int(ev.get("trips_per_day", TRIPS_PER_DAY))
    raw_records  = fetch_tlc_trips_lookback(lookback_days=lookback,
                                            trips_per_day=trips_per_day)
    print(f"Fetched {len(raw_records)} records ({lookback} day window, "
          f"{trips_per_day} trips/day)")

    adage_data = transform_to_adage(raw_records)
    print(f"Transformed {len(adage_data['events'])} events into ADAGE format")

    try:
        print(f"Saving to s3://{S3_BUCKET}/{S3_KEY}")
        save_to_s3(adage_data, S3_BUCKET, S3_KEY)
    except Exception as e:
        log_event("collect-nyc-tlc", "s3 save failed", level="ERROR",
                  context=context, event=ev,
                  duration_ms=(time.perf_counter() - t0) * 1000,
                  error_type=type(e).__name__)
        print("Failed to save to S3:", e)
        raise

    n = len(adage_data["events"])
    elapsed_ms = (time.perf_counter() - t0) * 1000
    log_event("collect-nyc-tlc", "collection complete", context=context, event=ev,
              duration_ms=elapsed_ms, records_collected=n, s3_key=S3_KEY)
    emit_embedded_metric(
        "Bravo",
        {"RecordsCollected": float(n)},
        {"Service": "collect-nyc-tlc", "Environment": deployment_env()},
    )
    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": json.dumps({
            "message": "Data collection complete",
            "records_collected": n,
            "s3_location": f"s3://{S3_BUCKET}/{S3_KEY}",
        }),
    }


if __name__ == "__main__":
    print("Running local test (simulating Lambda)...")
    response = lambda_handler(event={}, context=None)
    print("Lambda response:")
    print(json.dumps(response, indent=2))
