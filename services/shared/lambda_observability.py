"""Structured JSON logging and CloudWatch Embedded Metric Format (EMF) for Lambdas."""

from __future__ import annotations

import json
import os
import time
from typing import Any


def deployment_env() -> str:
    """Return logical environment (staging, prod, dev) from env vars."""
    return os.environ.get("ENV") or os.environ.get("ENVIRONMENT") or "dev"


def correlation_id(event: dict | None, context: Any) -> str:
    """Prefer API Gateway request id, else Lambda aws_request_id, else local."""
    if event:
        rc = event.get("requestContext")
        if isinstance(rc, dict):
            rid = rc.get("requestId") or rc.get("request_id")
            if rid:
                return str(rid)
    if context is not None and getattr(context, "aws_request_id", None):
        return context.aws_request_id
    return "local"


def log_event(
    service: str,
    message: str,
    *,
    level: str = "INFO",
    context: Any = None,
    event: dict | None = None,
    duration_ms: float | None = None,
    **fields: Any,
) -> None:
    """Emit one JSON log line for CloudWatch Logs Insights."""
    payload: dict[str, Any] = {
        "level": level,
        "service": service,
        "message": message,
        "env": deployment_env(),
    }
    if context is not None and getattr(context, "aws_request_id", None):
        payload["aws_request_id"] = context.aws_request_id
    payload["correlation_id"] = correlation_id(event if event is not None else {}, context)
    if duration_ms is not None:
        payload["duration_ms"] = round(duration_ms, 2)
    payload.update(fields)
    print(json.dumps(payload, default=str))


def emit_embedded_metric(
    namespace: str,
    metrics: dict[str, float],
    dimensions: dict[str, str] | None = None,
) -> None:
    """Emit a single EMF log line; CloudWatch extracts custom metrics automatically.

    See: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html
    """
    dims = dimensions or {}
    dim_names = list(dims.keys())
    metric_defs = []
    for name, _val in metrics.items():
        metric_defs.append({"Name": name, "Unit": "Count"})
    entry: dict[str, Any] = {
        "_aws": {
            "Timestamp": int(time.time() * 1000),
            "CloudWatchMetrics": [
                {
                    "Namespace": namespace,
                    "Dimensions": [dim_names] if dim_names else [],
                    "Metrics": metric_defs,
                }
            ],
        },
        **dims,
        **metrics,
    }
    print(json.dumps(entry))
