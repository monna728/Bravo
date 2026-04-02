"""Build JSON test reports and persist them to S3."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from shared.s3_uploader import put_json


def build_report(
    *,
    test_results: dict[str, Any],
    boroughs_tested: list[str],
    overall_pass: bool,
    overall_accuracy: float | None,
    threshold: float,
    warnings: list[str],
    data_points_summary: dict[str, Any],
) -> dict[str, Any]:
    """Assemble the full report dict (also written to S3)."""
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "boroughs_tested": boroughs_tested,
        "overall_pass": overall_pass,
        "overall_accuracy": overall_accuracy,
        "threshold_percent": threshold,
        "ground_truth_note": (
            "Backtest actuals use demand_proxy: min-max of trip_count on the training window only (0–100)."
        ),
        "data_points": data_points_summary,
        "warnings": warnings,
        "test_results": test_results,
    }


def save_report_to_s3(bucket: str, report: dict[str, Any]) -> str:
    """Upload ``report`` to ``s3://{bucket}/test-reports/report_<timestamp>.json``."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    key = f"test-reports/report_{ts}.json"
    put_json(bucket, key, report)
    return key
