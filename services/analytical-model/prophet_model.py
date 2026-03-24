"""Core prediction engine using Facebook Prophet.

Loads merged historical data from S3, builds a Prophet time-series model
with event count and weather as regressors, and produces a Crowd Demand
Index (0–100) for requested future dates and boroughs.

Weighted signals:
    - NYC taxi trip volume:  50%
    - Ticketmaster events:   30%
    - Weather impact:        20%
"""

import json
import os
from datetime import datetime, timedelta

import boto3
import pandas as pd

S3_BUCKET = os.environ.get("rushhour-data", "bucket-placeholder")
MERGED_PREFIX = "processed/merged"

VALID_BOROUGHS = {"Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"}

WEATHER_MULTIPLIERS = {
    "thunderstorm": 0.75,
    "snow": 0.75,
    "rain": 0.85,
    "showers": 0.85,
    "fog": 0.92,
    "cloudy": 1.0,
    "clear": 1.0,
    "unknown": 1.0,
}

TIME_OF_DAY_FACTORS = {
    "morning": 0.7,
    "afternoon": 0.9,
    "evening": 1.15,
    "night": 0.6,
    "all": 1.0,
}

SIGNAL_WEIGHTS = {
    "taxi": 0.50,
    "event": 0.30,
    "weather": 0.20,
}

DEFAULT_LOOKBACK_DAYS = 90
MIN_DATAPOINTS = 2


def get_weather_multiplier(condition: str) -> float:
    """Return demand multiplier for a weather condition."""
    return WEATHER_MULTIPLIERS.get(condition.lower(), 1.0) if condition else 1.0


def get_time_of_day_factor(time_of_day: str) -> float:
    """Return scaling factor for time-of-day period."""
    return TIME_OF_DAY_FACTORS.get(time_of_day.lower(), 1.0) if time_of_day else 1.0


def load_historical_data(
    borough: str,
    bucket: str = S3_BUCKET,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    end_date: str | None = None,
) -> list[dict]:
    """Load merged daily records from S3, filtered to a specific borough.

    Reads all files under processed/merged/ and returns events whose
    borough matches the requested borough within the lookback window.
    """
    s3 = boto3.client("s3")
    if end_date:
        ref_date = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        ref_date = datetime.utcnow()
    start = (ref_date - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=MERGED_PREFIX):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".json"):
                keys.append(obj["Key"])

    records = []
    for key in keys:
        obj = s3.get_object(Bucket=bucket, Key=key)
        data = json.loads(obj["Body"].read().decode("utf-8"))
        for event in data.get("events", []):
            attr = event.get("attribute", {})
            event_date = attr.get("date", "")
            event_borough = attr.get("borough", "") or attr.get("top_borough", "")

            if event_borough != borough:
                continue
            if event_date < start or event_date > ref_date.strftime("%Y-%m-%d"):
                continue

            records.append(attr)

    records.sort(key=lambda r: r.get("date", ""))
    return records


def build_prophet_dataframe(records: list[dict]) -> pd.DataFrame:
    """Convert merged daily records into a DataFrame suitable for Prophet.

    Columns: ds, y (trip_count), event_count, is_rainy, temperature_c
    """
    rows = []
    for r in records:
        weather = r.get("dominant_weather", "clear").lower()
        is_rainy = 1 if weather in ("rain", "showers", "thunderstorm", "snow") else 0

        rows.append({
            "ds": pd.Timestamp(r["date"]),
            "y": float(r.get("trip_count", 0)),
            "event_count": float(r.get("event_count", 0)),
            "is_rainy": float(is_rainy),
            "temperature_c": float(r.get("temperature_avg_c", 15.0)),
            "dominant_weather": weather,
            "active_events": int(r.get("event_count", 0)),
        })

    return pd.DataFrame(rows)


def fit_and_forecast(
    historical_df: pd.DataFrame,
    forecast_start: str,
    forecast_end: str,
) -> pd.DataFrame:
    """Fit a Prophet model on historical data and forecast future dates.

    Adds event_count, is_rainy, and temperature_c as regressors.
    Returns the forecast DataFrame with yhat, yhat_lower, yhat_upper.
    """
    from prophet import Prophet

    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=True,
        changepoint_prior_scale=0.05,
    )

    model.add_regressor("event_count")
    model.add_regressor("is_rainy")
    model.add_regressor("temperature_c")

    train_df = historical_df[["ds", "y", "event_count", "is_rainy", "temperature_c"]].copy()
    model.fit(train_df)

    start_dt = pd.Timestamp(forecast_start)
    end_dt = pd.Timestamp(forecast_end)
    num_days = (end_dt - start_dt).days + 1
    future = model.make_future_dataframe(periods=num_days, include_history=False)

    last_event_count = float(historical_df["event_count"].iloc[-1]) if len(historical_df) > 0 else 0.0
    last_is_rainy = float(historical_df["is_rainy"].iloc[-1]) if len(historical_df) > 0 else 0.0
    last_temp = float(historical_df["temperature_c"].iloc[-1]) if len(historical_df) > 0 else 15.0

    future["event_count"] = last_event_count
    future["is_rainy"] = last_is_rainy
    future["temperature_c"] = last_temp

    forecast = model.predict(future)
    return forecast


def normalise_to_index(
    yhat_values: list[float],
    historical_y: list[float],
) -> list[float]:
    """Normalise raw yhat predictions to a 0–100 demand index.

    Uses min-max scaling against historical y values.
    """
    if not historical_y:
        return [50.0] * len(yhat_values)

    hist_min = min(historical_y)
    hist_max = max(historical_y)

    if hist_max == hist_min:
        return [50.0] * len(yhat_values)

    normalised = []
    for val in yhat_values:
        score = ((val - hist_min) / (hist_max - hist_min)) * 100.0
        score = max(0.0, min(100.0, score))
        normalised.append(round(score, 1))

    return normalised


def calculate_contributing_factors(
    records: list[dict],
    historical_df: pd.DataFrame,
) -> dict:
    """Calculate the breakdown of signals contributing to the prediction.

    Returns taxi_signal (0–1), event_signal (0–1), weather_impact (0–1),
    and active_events count.
    """
    if historical_df.empty or not records:
        return {
            "taxi_signal": 0.0,
            "event_signal": 0.0,
            "weather_impact": 1.0,
            "active_events": 0,
        }

    max_trips = historical_df["y"].max()
    avg_trips = historical_df["y"].mean()
    taxi_signal = round(avg_trips / max_trips, 2) if max_trips > 0 else 0.0

    max_events = historical_df["event_count"].max()
    avg_events = historical_df["event_count"].mean()
    event_signal = round(avg_events / max_events, 2) if max_events > 0 else 0.0

    last_weather = records[-1].get("dominant_weather", "clear")
    weather_impact = get_weather_multiplier(last_weather)

    active_events = int(historical_df["active_events"].iloc[-1]) if len(historical_df) > 0 else 0

    return {
        "taxi_signal": taxi_signal,
        "event_signal": event_signal,
        "weather_impact": weather_impact,
        "active_events": active_events,
    }


def predict(
    borough: str,
    start_date: str,
    end_date: str,
    time_of_day: str = "all",
    event_type: str | None = None,
    bucket: str = S3_BUCKET,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> dict:
    """Generate Crowd Demand Index predictions for a borough and date range.

    """
    warnings = []

    records = load_historical_data(
        borough=borough,
        bucket=bucket,
        lookback_days=lookback_days,
        end_date=start_date,
    )

    if len(records) < MIN_DATAPOINTS:
        return {
            "status": "warning",
            "borough": borough,
            "message": f"Insufficient historical data for {borough} "
                       f"({len(records)} records found, need at least {MIN_DATAPOINTS}). "
                       "Returning estimated prediction.",
            "predictions": _fallback_predictions(start_date, end_date, time_of_day),
            "contributing_factors": {
                "taxi_signal": 0.0,
                "event_signal": 0.0,
                "weather_impact": 1.0,
                "active_events": 0,
            },
            "model_info": {
                "training_days": len(records),
                "borough": borough,
                "lookback_days": lookback_days,
            },
        }

    historical_df = build_prophet_dataframe(records)

    if len(historical_df) < MIN_DATAPOINTS:
        return {
            "status": "warning",
            "borough": borough,
            "message": "Insufficient data after processing. Returning estimated prediction.",
            "predictions": _fallback_predictions(start_date, end_date, time_of_day),
            "contributing_factors": calculate_contributing_factors(records, historical_df),
            "model_info": {
                "training_days": len(historical_df),
                "borough": borough,
                "lookback_days": lookback_days,
            },
        }

    try:
        forecast = fit_and_forecast(historical_df, start_date, end_date)
    except Exception as e:
        return {
            "status": "error",
            "borough": borough,
            "message": f"Prophet model fitting failed: {str(e)}",
            "predictions": _fallback_predictions(start_date, end_date, time_of_day),
            "contributing_factors": calculate_contributing_factors(records, historical_df),
            "model_info": {
                "training_days": len(historical_df),
                "borough": borough,
                "lookback_days": lookback_days,
            },
        }

    yhat_values = forecast["yhat"].tolist()
    yhat_lower = forecast["yhat_lower"].tolist()
    yhat_upper = forecast["yhat_upper"].tolist()
    forecast_dates = forecast["ds"].dt.strftime("%Y-%m-%d").tolist()

    historical_y = historical_df["y"].tolist()
    normalised_scores = normalise_to_index(yhat_values, historical_y)
    normalised_lower = normalise_to_index(yhat_lower, historical_y)
    normalised_upper = normalise_to_index(yhat_upper, historical_y)

    tod_factor = get_time_of_day_factor(time_of_day)
    last_weather = records[-1].get("dominant_weather", "clear") if records else "clear"
    weather_mult = get_weather_multiplier(last_weather)

    predictions = []
    for i, date_str in enumerate(forecast_dates):
        raw_score = normalised_scores[i]
        adjusted = raw_score * tod_factor * weather_mult
        adjusted = max(0.0, min(100.0, round(adjusted, 1)))

        lower = max(0.0, min(100.0, round(normalised_lower[i] * tod_factor * weather_mult, 1)))
        upper = max(0.0, min(100.0, round(normalised_upper[i] * tod_factor * weather_mult, 1)))

        predictions.append({
            "date": date_str,
            "demand_index": adjusted,
            "confidence_lower": lower,
            "confidence_upper": upper,
            "time_of_day": time_of_day,
            "weather_condition": last_weather,
            "weather_multiplier": weather_mult,
        })

    contributing = calculate_contributing_factors(records, historical_df)

    return {
        "status": "success",
        "borough": borough,
        "predictions": predictions,
        "contributing_factors": contributing,
        "model_info": {
            "training_days": len(historical_df),
            "borough": borough,
            "lookback_days": lookback_days,
        },
    }


def _fallback_predictions(
    start_date: str,
    end_date: str,
    time_of_day: str,
) -> list[dict]:
    """Generate placeholder predictions when the model can't run."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    predictions = []

    current = start
    while current <= end:
        predictions.append({
            "date": current.strftime("%Y-%m-%d"),
            "demand_index": 50.0,
            "confidence_lower": 30.0,
            "confidence_upper": 70.0,
            "time_of_day": time_of_day,
            "weather_condition": "unknown",
            "weather_multiplier": 1.0,
        })
        current += timedelta(days=1)

    return predictions
