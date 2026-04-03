"""
Test environment configuration for the data-collection microservice.

Testing Strategy: Two-layer approach
======================================

1. Sociable Unit Tests (every push/PR, fully offline)
  - External boundaries mocked: HTTP via unittest.mock, S3 via moto
  - Marker: default (no marker needed)

2. Integration Tests (merge to main only, real AWS)
  - HTTP APIs still mocked; real S3 bucket used
  - Only runs when --run-integration flag is passed
"""

import os
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "unit: fast offline sociable unit tests using moto",
    )
    config.addinivalue_line(
        "markers",
        "integration: tests that require real AWS credentials and S3 access",
    )


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests against real AWS (requires credentials)",
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless --run-integration flag is provided."""
    if not config.getoption("--run-integration"):
        skip = pytest.mark.skip(reason="Pass --run-integration to run against real AWS")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip)


@pytest.fixture()
def aws_credentials(monkeypatch):
    """Fake AWS credentials for moto — never reach real AWS."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("TICKETMASTER_API_KEY", "test-api-key")


@pytest.fixture()
def real_aws_credentials():
    """Check real AWS credentials exist — skip the test if they don't."""
    required = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        pytest.skip(f"Real AWS credentials missing: {missing}")


@pytest.fixture()
def real_s3_bucket():
    """Return the real S3 bucket name."""
    return os.environ.get("S3_BUCKET", "rushhour-data")