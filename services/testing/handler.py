"""Testing microservice: Lambda entrypoint and CLI for analytical model QA suites."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, ".."))
sys.path.insert(0, os.path.join(_ROOT, "..", "analytical-model"))

from prophet_model import VALID_BOROUGHS  # noqa: E402

from accuracy_tester import (  # noqa: E402
    run_compare_all_boroughs_test,
    run_confidence_interval_order_test,
    run_contract_test,
    run_insufficient_data_test,
    run_invalid_borough_http_test,
    run_regressor_impact_across_boroughs,
    run_score_bounds_test,
    run_weather_multiplier_test,
)
from backtester import run_walk_forward_backtest  # noqa: E402
from report_generator import build_report, save_report_to_s3  # noqa: E402

DEFAULT_BUCKET = os.environ.get("rushhour-data", os.environ.get("S3_BUCKET_NAME", "bucket-placeholder"))
ACC_THRESHOLD = 80.0


def _parse_body(event: dict) -> dict:
    if "body" in event and event["body"]:
        body = event["body"]
        if isinstance(body, str):
            return json.loads(body)
        return body
    return event


def _run_suites(
    bucket: str,
    borough: str | None,
    test_suite: str,
) -> tuple[dict[str, Any], bool, float | None, dict[str, Any]]:
    """Execute selected suites; returns (test_results, overall_pass, overall_accuracy, data_summary)."""
    results: dict[str, Any] = {}
    passes: list[bool] = []
    overall_acc: float | None = None
    data_summary: dict[str, Any] = {}

    b_list = [borough] if borough else sorted(VALID_BOROUGHS)

    run_accuracy = test_suite in ("all", "accuracy")
    run_edge = test_suite in ("all", "edge_cases")
    run_contract = test_suite in ("all", "contract")

    if run_accuracy:
        back = run_walk_forward_backtest(bucket, boroughs=b_list if borough else None)
        results["backtest"] = back
        passes.append(back.get("overall_pass", False))
        overall_acc = back.get("overall_accuracy")
        data_summary["backtest_boroughs"] = list(back.get("borough_results", {}).keys())
        for name, br in back.get("borough_results", {}).items():
            data_summary.setdefault("rows_per_borough", {})[name] = {
                "n_train": br.get("n_train"),
                "n_test": br.get("n_test"),
            }

        reg = run_regressor_impact_across_boroughs(bucket)
        results["regressor_impact"] = reg
        passes.append(reg.get("pass", False))

    if run_edge:
        results["insufficient_data"] = run_insufficient_data_test(bucket)
        passes.append(results["insufficient_data"].get("pass", False))

        results["invalid_borough_http"] = run_invalid_borough_http_test()
        passes.append(results["invalid_borough_http"].get("pass", False))

        results["score_bounds_50"] = run_score_bounds_test(bucket)
        passes.append(results["score_bounds_50"].get("pass", False))

        results["confidence_interval_order"] = run_confidence_interval_order_test(bucket)
        passes.append(results["confidence_interval_order"].get("pass", False))

        results["weather_multiplier"] = run_weather_multiplier_test(bucket)
        passes.append(results["weather_multiplier"].get("pass", False))

        results["compare_all_boroughs"] = run_compare_all_boroughs_test(bucket)
        passes.append(results["compare_all_boroughs"].get("pass", False))

    if run_contract:
        cb = borough or "Manhattan"
        results["api_contract"] = run_contract_test(bucket, borough=cb)
        passes.append(results["api_contract"].get("pass", False))

    overall_pass = all(passes) if passes else False
    return results, overall_pass, overall_acc, data_summary


def run_tests(
    bucket: str,
    borough: str | None,
    test_suite: str,
) -> dict[str, Any]:
    """Run tests and upload report; returns inner payload for API/CLI."""
    test_results, overall_pass, overall_acc, data_summary = _run_suites(bucket, borough, test_suite)

    boroughs_tested = [borough] if borough else sorted(VALID_BOROUGHS)
    warnings: list[str] = []
    if overall_acc is not None and overall_acc < ACC_THRESHOLD:
        warnings.append(f"Overall backtest accuracy {overall_acc}% is below {ACC_THRESHOLD}% threshold.")
    for name, tr in test_results.items():
        if isinstance(tr, dict) and tr.get("pass") is False and name == "backtest":
            warnings.append("One or more boroughs failed the ±15 point accuracy threshold.")

    report = build_report(
        test_results=test_results,
        boroughs_tested=boroughs_tested,
        overall_pass=overall_pass,
        overall_accuracy=overall_acc,
        threshold=ACC_THRESHOLD,
        warnings=warnings,
        data_points_summary=data_summary,
    )
    report_key = save_report_to_s3(bucket, report)

    return {
        "status": "pass" if overall_pass else "fail",
        "overall_accuracy": overall_acc,
        "threshold": ACC_THRESHOLD,
        "test_results": test_results,
        "report_s3_key": report_key,
    }


def lambda_handler(event: dict, context: Any) -> dict:
    """POST /test/predict body: ``borough`` (optional), ``test_suite`` (all|accuracy|edge_cases|contract)."""
    try:
        body = _parse_body(event)
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid JSON body"}),
        }

    bucket = body.get("bucket", DEFAULT_BUCKET)
    borough = body.get("borough")
    test_suite = body.get("test_suite", "all")
    if test_suite not in ("all", "accuracy", "edge_cases", "contract"):
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "test_suite must be all, accuracy, edge_cases, or contract"}),
        }

    payload = run_tests(bucket=bucket, borough=borough, test_suite=test_suite)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="RushHour analytical model testing microservice")
    parser.add_argument("--borough", default=None, help="Single borough (default: all boroughs for backtest)")
    parser.add_argument(
        "--suite",
        choices=["all", "accuracy", "edge_cases", "contract"],
        default="all",
        help="Which test suite to run",
    )
    parser.add_argument("--bucket", default=DEFAULT_BUCKET, help="S3 bucket for merged data and reports")
    args = parser.parse_args()
    out = run_tests(bucket=args.bucket, borough=args.borough, test_suite=args.suite)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
