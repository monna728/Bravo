"""Load merged historical demand features from S3 for model testing."""

from __future__ import annotations

MERGED_PREFIX = "processed/merged"


def load_merged_records_for_borough(bucket: str, borough: str) -> list[dict]:
    """Return sorted daily attribute dicts for ``borough`` from all merged JSON files under ``MERGED_PREFIX``."""
    from shared.s3_uploader import get_json, list_json_keys

    keys = list_json_keys(bucket, MERGED_PREFIX)
    records: list[dict] = []
    for key in keys:
        data = get_json(bucket, key)
        for event in data.get("events", []):
            attr = event.get("attribute", {})
            b = attr.get("borough", "") or attr.get("top_borough", "")
            if b != borough:
                continue
            records.append(attr)
    records.sort(key=lambda r: r.get("date", ""))
    return records
