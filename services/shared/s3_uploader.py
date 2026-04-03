"""Shared S3 helpers for JSON read/write and key listing."""

from __future__ import annotations

import json
from typing import Any

import boto3


def get_json(bucket: str, key: str) -> dict[str, Any]:
    """Download an S3 object and parse it as JSON."""
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(obj["Body"].read().decode("utf-8"))


def put_json(bucket: str, key: str, data: dict[str, Any], *, indent: int = 2) -> None:
    """Serialise ``data`` to JSON and upload to S3."""
    s3 = boto3.client("s3")
    body = json.dumps(data, indent=indent, default=str)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body.encode("utf-8"),
        ContentType="application/json",
    )


def list_json_keys(bucket: str, prefix: str) -> list[str]:
    """Return object keys under ``prefix`` ending in ``.json``."""
    s3 = boto3.client("s3")
    keys: list[str] = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            k = obj["Key"]
            if k.endswith(".json"):
                keys.append(k)
    return keys
