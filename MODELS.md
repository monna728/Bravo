# Dataset Structures/Layout

## ADAGE model JSON
{
  "data_source": "nyc_tlc",
  "dataset_type": "taxi_trips",
  "dataset_id": "s3://bucket-placeholder/tlc/raw/tlc_trips.json",
  "time_object": {
    "timestamp": "2026-03-15 17:00:00.000000",
    "timezone": "America/New_York"
  },
  "events": [
    {
      "time_object": {
        "timestamp": "2026-03-14 08:15:00.000000",
        "duration": 23.5,
        "duration_unit": "minute",
        "timezone": "America/New_York"
      },
      "event_type": "taxi_pickup",
      "attribute": {
        "vendorid": 2,
        "pulocationid": 161,
        "dolocationid": 230,
        "passenger_count": 1.0,
        "trip_distance": 4.8,
        "fare_amount": 18.5,
        "total_amount": 24.3,
        "payment_type": 1,
        "congestion_surcharge": 2.5,
        "ratecodeid": 1.0
      }
    }
  ]
}

