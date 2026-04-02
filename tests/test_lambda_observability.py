import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services"))
from shared.lambda_observability import (
    correlation_id,
    deployment_env,
    emit_embedded_metric,
    log_event,
)


class _Ctx:
    def __init__(self, rid="req-abc"):
        self.aws_request_id = rid


def test_deployment_env_prefers_env_var(monkeypatch):
    monkeypatch.setenv("ENV", "staging")
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    assert deployment_env() == "staging"


def test_deployment_env_fallback_environment(monkeypatch):
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "prod")
    assert deployment_env() == "prod"


def test_deployment_env_default(monkeypatch):
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    assert deployment_env() == "dev"


def test_correlation_id_api_gateway():
    event = {"requestContext": {"requestId": "gw-123"}}
    assert correlation_id(event, _Ctx()) == "gw-123"


def test_correlation_id_lambda_only():
    assert correlation_id({}, _Ctx("lam-456")) == "lam-456"


def test_correlation_id_local():
    assert correlation_id({}, None) == "local"


def test_log_event_json_and_correlation(capsys):
    log_event(
        "test-svc",
        "hello",
        context=_Ctx("rid-1"),
        event={"requestContext": {"requestId": "gw-9"}},
        extra_field=42,
    )
    out = capsys.readouterr().out.strip()
    row = json.loads(out)
    assert row["service"] == "test-svc"
    assert row["message"] == "hello"
    assert row["correlation_id"] == "gw-9"
    assert row["aws_request_id"] == "rid-1"
    assert row["extra_field"] == 42


def test_emit_embedded_metric_contains_aws_and_metrics(capsys):
    emit_embedded_metric(
        "Bravo",
        {"PredictionsGenerated": 3.0},
        {"Borough": "Manhattan", "Environment": "dev"},
    )
    out = capsys.readouterr().out.strip()
    row = json.loads(out)
    assert "_aws" in row
    assert row["PredictionsGenerated"] == 3.0
    assert row["Borough"] == "Manhattan"
    assert any(
        m["Namespace"] == "Bravo"
        for m in row["_aws"]["CloudWatchMetrics"]
    )
