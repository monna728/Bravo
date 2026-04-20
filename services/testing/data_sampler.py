"""Load merged historical demand features from S3 for model testing."""

from __future__ import annotations

MERGED_PREFIX = "processed/merged"


def load_merged_records_for_borough(bucket: str, borough: str) -> list[dict]:
    """Return one latest, taxi-backed record per date for ``borough``.

    Preprocessing can produce Manhattan-only rows for dates that have weather/events
    but no taxi observations. Those rows have no ground-truth demand target and can
    poison backtests, so we keep only records where ``sources_present`` includes
    ``nyc_tlc``.

    If multiple merged snapshots contain the same borough/date, the newest key wins.
    """
    from shared.s3_uploader import get_json, list_json_keys

    keys = sorted(list_json_keys(bucket, MERGED_PREFIX))
    by_date: dict[str, dict] = {}
    for key in keys:
        data = get_json(bucket, key)
        for event in data.get("events", []):
            attr = event.get("attribute", {})
            b = attr.get("borough", "") or attr.get("top_borough", "")
            if b != borough:
                continue
            date_str = str(attr.get("date", "")).strip()
            if not date_str:
                continue
            sources = attr.get("sources_present", [])
            if isinstance(sources, str):
                sources = [sources]
            if "nyc_tlc" not in set(sources):
                continue
            by_date[date_str] = attr

    records = [by_date[d] for d in sorted(by_date)]
    return records
