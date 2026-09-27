"""Each rule's field access checked against the real raw events captured
live in the detection session (see ../../input.json and
.planning/self-healing-system-planning.md). This is what caught EC2-1's
requestParameters being nested one level deeper than the other four rules
-- a bug that would only have shown up on a live run, not in the fake
event fixtures used by test_rules.py."""

import json
from pathlib import Path

import pytest

INPUT = Path(__file__).resolve().parents[2] / "input.json"

pytestmark = pytest.mark.skipif(not INPUT.is_file(), reason="input.json not captured")


@pytest.fixture(scope="module")
def captured():
    return json.load(open(INPUT))["violation_events"]


@pytest.mark.parametrize(
    "rule, field_path",
    [
        ("S3-1", ["bucketName"]),
        ("SG-1", ["groupId"]),
        ("RDS-1", ["dBInstanceIdentifier"]),
        ("EC2-1", ["ModifyInstanceMetadataOptionsRequest", "InstanceId"]),
        ("CT-1", ["name"]),
    ],
)
def test_the_field_our_rule_reads_exists_in_the_real_event(captured, rule, field_path):
    params = captured[rule][0]["detail"]["requestParameters"]
    for key in field_path:
        params = params[key]
    assert params
