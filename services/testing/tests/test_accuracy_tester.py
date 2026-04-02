"""Unit tests for the testing microservice (metrics, suites with mocks — no real AWS)."""

from __future__ import annotations

import json
import os
import sys

import boto3
import pytest
from moto import mock_aws

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_SERVICES = os.path.join(_ROOT, "..")
# analytical-model must not shadow ``handler``: resolve testing ``handler.py`` first.
sys.path.insert(0, os.path.join(_SERVICES, "analytical-model"))
sys.path.insert(0, _SERVICES)
sys.path.insert(0, _ROOT)

from metrics import (  # noqa: E402
    calculate_accuracy,
    calculate_directional_accuracy,
    calculate_mae,
    calculate_mape,
    calculate_rmse,
    score_summary,
)


def test_calculate_accuracy_within_tolerance():
    assert calculate_accuracy([50.0, 50.0], [55.0, 40.0], tolerance=15.0) == 100.0


def test_calculate_accuracy_partial():
    assert calculate_accuracy([50.0, 50.0], [80.0, 40.0], tolerance=15.0) == 50.0


def test_mae_rmse():
    assert calculate_mae([10.0, 20.0], [12.0, 18.0]) == 2.0
    assert calculate_rmse([0.0, 0.0], [3.0, 4.0]) == pytest.approx(3.5355, rel=1e-3)


def test_mape_skips_zero_actual():
    assert calculate_mape([0.0, 100.0], [10.0, 90.0]) == pytest.approx(10.0)


def test_directional_accuracy():
    # up then up
    assert calculate_directional_accuracy([10.0, 20.0, 30.0], [5.0, 15.0, 25.0]) == 100.0


def test_score_summary_flags():
    s = score_summary([50.0] * 10, [52.0] * 10)
    assert s["accuracy_pass"] is True
    assert "mae" in s


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@mock_aws
def test_handler_contract_suite_runs(aws_credentials):
    import boto3

    from handler import lambda_handler

    boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="t-bucket")
    event = {"body": json.dumps({"test_suite": "contract", "bucket": "t-bucket"})}
    resp = lambda_handler(event, None)

    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert "test_results" in body
    assert body["test_results"].get("api_contract") is not None
    assert body["test_results"]["api_contract"].get("pass") is True
