"""
Sprint 1 Demo — End-to-End Pipeline Demonstration
===================================================
Simulates the full pipeline locally using moto (mock S3).
No AWS credentials, no API keys, no internet required.

Run:  python demo.py

Pipeline:
  1. Data Collection   — generates realistic mock data for all 3 sources
  2. Data Preprocessing — normalises and merges by date
  3. Data Retrieval     — queries merged data by borough + date range
  4. Analytical Model   — predicts Crowd Demand Index (0–100)
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from unittest.mock import patch

import boto3
import pandas as pd
from moto import mock_aws

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services", "data-collection"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services", "data-preprocessing"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services", "data-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services", "analytical-model"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services"))

BUCKET = "bravo-demo-bucket"
BOROUGHS = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]

SEPARATOR = "=" * 70


def print_header(step_num: int, title: str):
    print(f"\n{SEPARATOR}")
    print(f"  STEP {step_num}: {title}")
    print(SEPARATOR)


def print_item(label: str, value):
    print(f"    {label}: {value}")


def print_json_preview(data: dict, max_keys: int = 6):
    """Print a compact preview of a dict."""
    for i, (k, v) in enumerate(data.items()):
        if i >= max_keys:
            print(f"    ... and {len(data) - max_keys} more fields")
            break
        if isinstance(v, list):
            print(f"    {k}: [{len(v)} items]")
        elif isinstance(v, dict):
            print(f"    {k}: {{...}}")
        else:
            print(f"    {k}: {v}")


# ── Mock Data Generators ────────────────────────────────────────────────────

def generate_ticketmaster_data() -> dict:
    """Generate realistic Ticketmaster ADAGE data."""
    base = datetime(2026, 4, 15)
    events = [
        ("Rock Concert at MSG", "concert", "2026-04-15T20:00:00Z"),
        ("Knicks vs Lakers", "sports", "2026-04-15T19:30:00Z"),
        ("Broadway: Hamilton", "arts_theatre", "2026-04-15T14:00:00Z"),
        ("Jazz Night Brooklyn", "concert", "2026-04-16T21:00:00Z"),
        ("Yankees vs Red Sox", "sports", "2026-04-16T18:00:00Z"),
        ("Spring Food Festival", "other", "2026-04-16T10:00:00Z"),
        ("Nets vs Celtics", "sports", "2026-04-17T19:00:00Z"),
    ]

    adage_events = []
    for name, etype, ts in events:
        adage_events.append({
            "time_object": {"timestamp": ts, "duration": 0, "duration_unit": "hour", "timezone": "America/New_York"},
            "event_type": etype,
            "attribute": {
                "event_id": f"TM-{hash(name) % 100000:05d}",
                "event_name": name,
                "venue_name": "NYC Venue",
                "city": "New York",
            },
        })

    return {
        "data_source": "ticketmaster",
        "dataset_type": "public_events",
        "dataset_id": f"s3://{BUCKET}/ticketmaster/raw/demo.json",
        "time_object": {"timestamp": "2026-04-15 00:00:00.000000", "timezone": "America/New_York"},
        "events": adage_events,
    }


def generate_taxi_data() -> dict:
    """Generate realistic NYC taxi trip ADAGE data across multiple boroughs.

    Day 1 (Apr 15): Manhattan dominates — big event night
    Day 2 (Apr 16): Brooklyn dominates — Brooklyn events
    Day 3 (Apr 17): Queens dominates — outer borough surge
    """
    base = datetime(2026, 4, 15)
    trips = []

    day_borough_configs = {
        0: [("Manhattan", 162, 10), ("Brooklyn", 61, 3), ("Queens", 129, 2)],
        1: [("Manhattan", 230, 3), ("Brooklyn", 61, 8), ("Brooklyn", 123, 4), ("Bronx", 69, 2)],
        2: [("Manhattan", 162, 2), ("Queens", 129, 9), ("Bronx", 69, 3), ("Staten Island", 23, 2)],
    }

    for day_offset, configs in day_borough_configs.items():
        for borough, loc_id, count in configs:
            for i in range(count):
                dt = base + timedelta(days=day_offset, hours=8 + i, minutes=i * 7)
                ts = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                dropoff = (dt + timedelta(minutes=12 + i * 3)).strftime("%Y-%m-%d %H:%M:%S.%f")
                duration = 12.0 + i * 3.0

                trips.append({
                    "time_object": {
                        "timestamp": ts, "duration": duration,
                        "duration_unit": "minute", "timezone": "America/New_York",
                    },
                    "event_type": "taxi_pickup",
                    "attribute": {
                        "vendorid": 1,
                        "pickup_locationid": loc_id,
                        "pickup_zone": f"Zone-{loc_id}",
                        "pickup_borough": borough,
                        "dropoff_locationid": loc_id + 1,
                        "dropoff_zone": f"Zone-{loc_id + 1}",
                        "dropoff_borough": borough,
                        "passenger_count": 2.0,
                        "trip_distance": round(3.5 + i * 0.5, 1),
                        "fare_amount": round(12.0 + i * 2.5, 2),
                        "total_amount": round(15.0 + i * 3.0, 2),
                        "payment_type": 1,
                        "congestion_surcharge": 2.5,
                        "ratecodeid": 1.0,
                    },
                })

    return {
        "data_source": "nyc_tlc",
        "dataset_type": "taxi_trips",
        "dataset_id": f"s3://{BUCKET}/tlc/raw/demo.json",
        "time_object": {"timestamp": "2026-04-15 00:00:00.000000", "timezone": "America/New_York"},
        "events": trips,
    }


def generate_weather_data() -> dict:
    """Generate realistic Open-Meteo ADAGE data (3 days x 24 hours)."""
    base = datetime(2026, 4, 15)
    events = []

    weather_patterns = [
        ("clear", 0.0, 1.0),
        ("clear", 0.0, 1.0),
        ("cloudy", 0.0, 1.0),
        ("rain", 2.5, 1.15),
    ]

    for day in range(3):
        for hour in range(24):
            dt = base + timedelta(days=day, hours=hour)
            pattern_idx = (day + hour // 8) % len(weather_patterns)
            category, precip, modifier = weather_patterns[pattern_idx]
            temp = 12.0 + (hour / 3.0) - (day * 2.0)

            events.append({
                "time_object": {
                    "timestamp": dt.strftime("%Y-%m-%dT%H:%M"),
                    "duration": 1, "duration_unit": "hour",
                    "timezone": "America/New_York",
                },
                "event_type": "weather_forecast",
                "attribute": {
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "precipitation_mm": precip,
                    "temperature_c": round(temp, 1),
                    "precipitation_probability": 30 if precip > 0 else 5,
                    "demand_modifier": modifier,
                    "weather_category": category,
                },
            })

    return {
        "data_source": "open_meteo",
        "dataset_type": "weather_forecast",
        "dataset_id": f"s3://{BUCKET}/weather/raw/demo.json",
        "time_object": {"timestamp": "2026-04-15 00:00:00.000000", "timezone": "America/New_York"},
        "events": events,
    }


# ── Pipeline Steps ──────────────────────────────────────────────────────────

def step1_collect(s3) -> tuple[dict, dict, dict]:
    """Simulate data collection: generate and store ADAGE data in S3."""
    print_header(1, "DATA COLLECTION")
    print("  Simulating data collection from 3 external APIs...\n")

    tm_data = generate_ticketmaster_data()
    taxi_data = generate_taxi_data()
    weather_data = generate_weather_data()

    s3.put_object(Bucket=BUCKET, Key="ticketmaster/raw/events_NYC_20260415.json",
                  Body=json.dumps(tm_data), ContentType="application/json")
    print_item("Ticketmaster", f"{len(tm_data['events'])} events collected (concerts, sports, arts)")

    s3.put_object(Bucket=BUCKET, Key="tlc/raw/trips_202604_20260415.json",
                  Body=json.dumps(taxi_data), ContentType="application/json")
    print_item("NYC Taxi (TLC)", f"{len(taxi_data['events'])} trip records collected across 5 boroughs")

    s3.put_object(Bucket=BUCKET, Key="weather/raw/weather_40.7_-74.0_20260415.json",
                  Body=json.dumps(weather_data), ContentType="application/json")
    print_item("Open-Meteo Weather", f"{len(weather_data['events'])} hourly readings (3 days)")

    print(f"\n  All data stored to mock S3 in ADAGE 3.0 format")
    print(f"  Bucket: {BUCKET}")

    return tm_data, taxi_data, weather_data


def step2_preprocess(s3, tm_data, taxi_data, weather_data):
    """Run the preprocessing pipeline: normalise + merge."""
    print_header(2, "DATA PREPROCESSING")
    print("  Normalising raw data from each source...\n")

    from normaliser import normalise_ticketmaster, normalise_nyc_taxi, normalise_weather
    from merger import merge_by_date, merged_to_adage

    tm_daily = normalise_ticketmaster(tm_data)
    print_item("Ticketmaster normalised", f"{len(tm_daily)} daily records")
    for rec in tm_daily:
        print(f"      {rec['date']}: {rec['event_count']} events — {', '.join(rec['event_names'][:3])}")

    taxi_daily = normalise_nyc_taxi(taxi_data)
    print_item("NYC Taxi normalised", f"{len(taxi_daily)} per-borough daily records")
    for rec in taxi_daily:
        print(f"      {rec['date']} [{rec['borough']}]: {rec['trip_count']} trips")

    weather_daily = normalise_weather(weather_data)
    print_item("Weather normalised", f"{len(weather_daily)} daily records")
    for rec in weather_daily:
        print(f"      {rec['date']}: {rec['temperature_avg_c']}C, {rec['dominant_weather']}")

    print("\n  Merging all sources by (date, borough)...")
    merged = merge_by_date(tm_daily, taxi_daily, weather_daily)
    print_item("Merged records", f"{len(merged)} per-borough daily records")

    print("\n  Sample merged records:")
    for sample in merged[:4]:
        print(f"      {sample['date']} [{sample['borough']}]: "
              f"{sample['event_count']} events, {sample['trip_count']} trips, "
              f"{sample['temperature_avg_c']}C {sample['dominant_weather']}")

    adage_merged = merged_to_adage(merged, bucket=BUCKET)
    s3_key = "processed/merged/merged_NYC_demo.json"
    s3.put_object(Bucket=BUCKET, Key=s3_key,
                  Body=json.dumps(adage_merged), ContentType="application/json")
    print(f"\n  Merged ADAGE output saved to s3://{BUCKET}/{s3_key}")

    return merged, adage_merged


def step3_retrieve(s3):
    """Query the merged data using the retrieval service."""
    print_header(3, "DATA RETRIEVAL")
    print("  Querying stored data via the retrieval service...\n")

    from s3_reader import retrieve

    print("  Query 1: All merged data")
    result = retrieve(source="merged", bucket=BUCKET)
    print_item("Records found", result["count"])
    print_item("Borough filter", result["borough"])

    print("\n  Query 2: Manhattan only, April 15-16")
    result_m = retrieve(source="merged", bucket=BUCKET, borough="Manhattan",
                        start_date="2026-04-15", end_date="2026-04-16")
    print_item("Records found", result_m["count"])
    print_item("Borough", result_m["borough"])
    for rec in result_m["records"]:
        attr = rec["attribute"]
        print(f"      {attr['date']}: {attr['trip_count']} trips, "
              f"{attr['event_count']} events, {attr['dominant_weather']}")

    print("\n  Query 3: Brooklyn only")
    result_b = retrieve(source="merged", bucket=BUCKET, borough="Brooklyn")
    print_item("Records found", result_b["count"])

    print("\n  Query 4: All raw ticketmaster events")
    result_t = retrieve(source="ticketmaster", bucket=BUCKET)
    print_item("Ticketmaster events found", result_t["count"])

    return result_m


def step4_predict(s3, merged_records):
    """Run the analytical model to produce a Crowd Demand Index."""
    print_header(4, "ANALYTICAL MODEL — CROWD DEMAND INDEX")
    print("  Loading historical data and generating predictions...\n")

    from prophet_model import (
        build_prophet_dataframe,
        normalise_to_index,
        calculate_contributing_factors,
        get_weather_multiplier,
        get_time_of_day_factor,
        load_historical_data,
    )

    records = load_historical_data("Manhattan", bucket=BUCKET, end_date="2026-04-18")

    if not records:
        print("  No historical data found — using merged records directly")
        records = [ev["attribute"] for ev in
                   json.loads(s3.get_object(Bucket=BUCKET,
                   Key="processed/merged/merged_NYC_demo.json")["Body"].read())
                   .get("events", [])
                   if ev.get("attribute", {}).get("borough") == "Manhattan"]

    if records:
        df = build_prophet_dataframe(records)
        print_item("Training data points", len(df))
        print_item("Date range", f"{df['ds'].min().date()} to {df['ds'].max().date()}")
        print_item("Avg daily trips", f"{df['y'].mean():.0f}")
        print_item("Avg daily events", f"{df['event_count'].mean():.1f}")

        historical_y = df["y"].tolist()
        simulated_yhat = [float(df["y"].mean() * 1.1)]
        scores = normalise_to_index(simulated_yhat, historical_y)

        weather_cond = records[-1].get("dominant_weather", "clear")
        weather_mult = get_weather_multiplier(weather_cond)
        tod_factor = get_time_of_day_factor("evening")

        final_score = min(100.0, max(0.0, round(scores[0] * weather_mult * tod_factor, 1)))

        factors = calculate_contributing_factors(records, df)

        print(f"\n  {'-' * 50}")
        print(f"  PREDICTION RESULT")
        print(f"  {'-' * 50}")
        print_item("Borough", "Manhattan")
        print_item("Date", "2026-04-18")
        print_item("Time of Day", "evening")
        print(f"\n    Crowd Demand Index:  {final_score} / 100")
        print(f"\n  Contributing Factors:")
        print_item("Taxi Signal", f"{factors['taxi_signal']}")
        print_item("Event Signal", f"{factors['event_signal']}")
        print_item("Weather Impact", f"{factors['weather_impact']} ({weather_cond})")
        print_item("Weather Multiplier", f"{weather_mult}")
        print_item("Time-of-Day Factor", f"{tod_factor} (evening)")
        print_item("Active Events", f"{factors['active_events']}")

        print(f"\n  Signal Weights:")
        print_item("Taxi volume", "50%")
        print_item("Event count", "30%")
        print_item("Weather impact", "20%")

        print(f"\n  {'-' * 50}")
        print(f"  Compare All Boroughs:")
        print(f"  {'-' * 50}")
        for borough in BOROUGHS:
            b_records = [ev["attribute"] for ev in
                         json.loads(s3.get_object(Bucket=BUCKET,
                         Key="processed/merged/merged_NYC_demo.json")["Body"].read())
                         .get("events", [])
                         if ev.get("attribute", {}).get("borough") == borough]
            if b_records:
                b_df = build_prophet_dataframe(b_records)
                b_yhat = [float(b_df["y"].mean() * 1.1)]
                b_scores = normalise_to_index(b_yhat, b_df["y"].tolist())
                b_score = min(100.0, max(0.0, round(b_scores[0] * weather_mult, 1)))
                trips = int(b_df["y"].mean())
                print(f"    {borough:20s}  Score: {b_score:5.1f}/100  (avg {trips} trips/day)")
            else:
                print(f"    {borough:20s}  No data")
    else:
        print("  Could not load data for prediction demo.")


def step5_interactive(s3):
    """Interactive prediction — user picks a date and time of day."""
    from prophet_model import (
        build_prophet_dataframe,
        normalise_to_index,
        calculate_contributing_factors,
        get_weather_multiplier,
        get_time_of_day_factor,
        VALID_BOROUGHS,
        TIME_OF_DAY_FACTORS,
    )

    print_header(5, "INTERACTIVE PREDICTION")
    print("  Try your own date and time-of-day to see demand scores.\n")
    print("  Available dates: 2026-04-15, 2026-04-16, 2026-04-17")
    print("  Time options: morning, afternoon, evening, night, all")
    print("  (Press Enter to skip and use defaults, or type 'q' to skip this step)\n")

    while True:
        user_date = input("  Enter date (YYYY-MM-DD): ").strip()
        if user_date.lower() == "q":
            print("\n  Skipping interactive prediction.")
            return
        if not user_date:
            user_date = "2026-04-16"
            print(f"    Using default: {user_date}")

        user_tod = input("  Enter time of day (morning/afternoon/evening/night/all): ").strip().lower()
        if user_tod.lower() == "q":
            print("\n  Skipping interactive prediction.")
            return
        if not user_tod or user_tod not in TIME_OF_DAY_FACTORS:
            user_tod = "evening"
            print(f"    Using default: {user_tod}")

        tod_factor = get_time_of_day_factor(user_tod)

        merged_data = json.loads(
            s3.get_object(Bucket=BUCKET, Key="processed/merged/merged_NYC_demo.json")["Body"].read()
        )
        all_events = merged_data.get("events", [])

        print(f"\n  {'-' * 58}")
        print(f"  DEMAND FORECAST: {user_date} ({user_tod})")
        print(f"  {'-' * 58}")
        print(f"  {'Borough':20s}  {'Score':>7s}  {'Trips':>7s}  {'Events':>7s}  {'Weather':>12s}")
        print(f"  {'-------':20s}  {'-----':>7s}  {'-----':>7s}  {'------':>7s}  {'-------':>12s}")

        any_data = False
        for borough in sorted(VALID_BOROUGHS):
            b_records = [ev["attribute"] for ev in all_events
                         if ev.get("attribute", {}).get("borough") == borough]

            if not b_records:
                print(f"  {borough:20s}  {'--':>7s}  {'--':>7s}  {'--':>7s}  {'no data':>12s}")
                continue

            any_data = True
            b_df = build_prophet_dataframe(b_records)

            date_record = next((r for r in b_records if r.get("date") == user_date), None)
            if date_record:
                trips = int(date_record.get("trip_count", 0))
                events = int(date_record.get("event_count", 0))
                weather = date_record.get("dominant_weather", "clear")
            else:
                trips = int(b_df["y"].mean())
                events = int(b_df["event_count"].mean())
                weather = b_records[-1].get("dominant_weather", "clear")

            weather_mult = get_weather_multiplier(weather)
            event_boost = 1.0 + events * 0.08
            trip_ratio = trips / max(b_df["y"].max(), 1)
            raw_score = (trip_ratio * 50 + min(events * 10, 40) + 10) * event_boost
            score = min(100.0, max(0.0, round(raw_score * weather_mult * tod_factor, 1)))

            print(f"  {borough:20s}  {score:6.1f}%  {trips:>7d}  {events:>7d}  {weather:>12s}")

        if not any_data:
            print("\n  No data available for any borough.")

        print(f"  {'-' * 58}")
        print(f"  Time-of-day factor ({user_tod}): x{tod_factor}")
        print(f"  Weather multiplier applied per borough")

        again = input("\n  Try another date/time? (y/n): ").strip().lower()
        if again != "y":
            break

    print("")


# ── Main ────────────────────────────────────────────────────────────────────

@mock_aws
def main():
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["rushhour-data"] = BUCKET

    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket=BUCKET)

    print("\n" + SEPARATOR)
    print("  EVENT INTELLIGENCE APPLICATION — Sprint 1 Demo")
    print("  Predictive Demand Intelligence for Ride-Sharing Operators")
    print(SEPARATOR)
    print(f"  Team: Bravo")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Pipeline: Collection -> Preprocessing -> Retrieval -> Prediction")

    tm, taxi, weather = step1_collect(s3)
    merged, adage_merged = step2_preprocess(s3, tm, taxi, weather)
    retrieval_result = step3_retrieve(s3)
    step4_predict(s3, merged)
    step5_interactive(s3)

    print(f"\n{SEPARATOR}")
    print("  DEMO COMPLETE")
    print(SEPARATOR)
    print("  All 4 microservices executed successfully.")
    print("  Data flowed: Collection -> Preprocessing -> Retrieval -> Prediction")
    print(f"  Total records processed: {len(tm['events'])} events + "
          f"{len(taxi['events'])} trips + {len(weather['events'])} weather readings")
    print(f"{SEPARATOR}\n")


if __name__ == "__main__":
    main()
