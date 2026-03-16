"""Convert ADAGE 3.0 JSON data to CSV format."""

import json
import pandas as pd
from datetime import datetime


def adage3_to_dataframe(data: dict) -> pd.DataFrame:
    """Convert an ADAGE 3.0 dict into a pandas DataFrame.

    Each event's attributes become columns, indexed by the event timestamp.
    """
    attributes = []
    timestamps = []

    for event in data.get("events", []):
        attributes.append(event.get("attribute", {}))
        timestamps.append(event.get("time_object", {}).get("timestamp", ""))

    df = pd.DataFrame(attributes)

    timestamp_format = "%Y-%m-%d %H:%M:%S.%f"
    try:
        parsed = [datetime.strptime(ts, timestamp_format) for ts in timestamps]
    except (ValueError, TypeError):
        parsed = timestamps

    df.index = parsed
    df.index.name = "timestamp"

    return df


def adage3_json_to_csv(filepath: str, csv_name: str = "output") -> pd.DataFrame:
    """Load an ADAGE 3.0 JSON file and save its events as CSV.

    Returns the DataFrame for further use.
    """
    with open(filepath, "r") as f:
        data = json.load(f)

    df = adage3_to_dataframe(data)
    df.to_csv(f"{csv_name}.csv")
    return df


def adage3_dict_to_csv(data: dict, csv_path: str) -> pd.DataFrame:
    """Convert an ADAGE 3.0 dict directly to CSV.

    Returns the DataFrame for further use.
    """
    df = adage3_to_dataframe(data)
    df.to_csv(csv_path)
    return df
