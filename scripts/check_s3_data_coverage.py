#!/usr/bin/env python3
"""List S3 raw/merged JSON and count distinct calendar dates per prefix (run from repo root).

Usage:
  python scripts/check_s3_data_coverage.py
  python scripts/check_s3_data_coverage.py --bucket my-bucket
"""

from __future__ import annotations

import argparse
import json
import os
import sys

try:
    import boto3
except ImportError:
    print("Install boto3: pip install boto3", file=sys.stderr)
    sys.exit(1)

DEFAULT_BUCKET = os.environ.get("S3_BUCKET_NAME", "rushhour-data")

PREFIXES: dict[str, str] = {
    "nyc_tlc": "tlc/raw",
    "open_meteo": "weather/raw",
    "ticketmaster": "ticketmaster/raw",
    "merged": "processed/merged",
}


def _event_date(ev: dict) -> str | None:
    ts = (ev.get("time_object") or {}).get("timestamp", "")
    if not ts:
        return None
    s = str(ts).strip()
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return None


def main() -> None:
    p = argparse.ArgumentParser(description="Check distinct dates in S3 ADAGE files.")
    p.add_argument("--bucket", default=DEFAULT_BUCKET, help="S3 bucket name")
    args = p.parse_args()
    bucket = args.bucket

    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")

    for source, prefix in PREFIXES.items():
        keys = [
            o["Key"]
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix)
            for o in page.get("Contents", [])
            if o["Key"].endswith(".json")
        ]
        print(f"\n=== {source} ({len(keys)} files under {prefix}/) ===")
        if not keys:
            print("  NO FILES FOUND")
            continue

        dates: set[str] = set()
        for key in keys:
            try:
                body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
                data = json.loads(body)
                for ev in data.get("events", []):
                    d = _event_date(ev)
                    if d:
                        dates.add(d)
                    attr = ev.get("attribute") or {}
                    if attr.get("date"):
                        dates.add(str(attr["date"])[:10])
            except Exception as exc:
                print(f"  ERROR reading {key}: {exc}")

        if dates:
            n = len(dates)
            lo, hi = min(dates), max(dates)
            ok = n >= 90
            flag = "YES" if ok else "NO — need more data"
            print(f"  Distinct dates : {n}")
            print(f"  Earliest       : {lo}")
            print(f"  Latest         : {hi}")
            print(f"  >= 90 days?    : {flag}")
        else:
            print("  Files exist but contain no events with parseable dates")


if __name__ == "__main__":
    main()
