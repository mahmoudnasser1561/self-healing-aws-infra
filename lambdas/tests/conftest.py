import pytest
from moto import mock_aws

PREFIX = "self-healing-aws-infra-"
ACCOUNT = "123456789012"
CI_ROLE = f"arn:aws:iam::{ACCOUNT}:role/{PREFIX}github-actions"


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.setenv(name, "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("PROJECT_PREFIX", PREFIX)


@pytest.fixture
def cloud(aws_env):
    with mock_aws():
        yield
