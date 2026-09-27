import json

import boto3

from conftest import CI_ROLE, PREFIX
import handler


def event(name, params=None, role=None, event_id="evt-1"):
    identity = {"arn": "arn:aws:iam::123456789012:user/admin"}
    if role:
        identity = {
            "arn": "arn:aws:sts::123456789012:assumed-role/x/session",
            "sessionContext": {"sessionIssuer": {"arn": role}},
        }
    return {
        "detail": {
            "eventID": event_id,
            "eventName": name,
            "eventTime": "2026-09-27T10:00:00Z",
            "userIdentity": identity,
            "requestParameters": params or {},
        }
    }


def setup(monkeypatch, cloud):
    topic = boto3.client("sns").create_topic(Name="alerts")["TopicArn"]
    monkeypatch.setenv("TOPIC_ARN", topic)
    monkeypatch.setenv("EXEMPT_ROLE_ARNS", CI_ROLE)
    return topic


def inbox(topic):
    sqs = boto3.client("sqs")
    queue = sqs.create_queue(QueueName="inbox")["QueueUrl"]
    arn = sqs.get_queue_attributes(QueueUrl=queue, AttributeNames=["QueueArn"])[
        "Attributes"
    ]["QueueArn"]
    boto3.client("sns").subscribe(
        TopicArn=topic,
        Protocol="sqs",
        Endpoint=arn,
        Attributes={"RawMessageDelivery": "true"},
    )
    return lambda: sqs.receive_message(QueueUrl=queue, MaxNumberOfMessages=10).get(
        "Messages", []
    )


def test_an_event_nobody_has_a_rule_for_is_dropped_quietly(cloud, monkeypatch, capsys):
    setup(monkeypatch, cloud)

    handler.handler(event("PutBucketVersioning", {"bucketName": f"{PREFIX}frontend"}))

    assert capsys.readouterr().out == ""


def test_a_change_by_an_exempt_role_is_dropped(cloud, monkeypatch, capsys):
    topic = setup(monkeypatch, cloud)
    receive = inbox(topic)
    bucket = f"{PREFIX}frontend-123456789012"
    boto3.client("s3").create_bucket(Bucket=bucket)
    boto3.client("s3").delete_public_access_block(Bucket=bucket)

    handler.handler(
        event("DeleteBucketPublicAccessBlock", {"bucketName": bucket}, role=CI_ROLE)
    )

    assert capsys.readouterr().out == ""
    assert receive() == []


def test_a_real_violation_is_fixed_notified_and_logged(cloud, monkeypatch, capsys):
    topic = setup(monkeypatch, cloud)
    receive = inbox(topic)
    bucket = f"{PREFIX}frontend-123456789012"
    boto3.client("s3").create_bucket(Bucket=bucket)
    boto3.client("s3").delete_public_access_block(Bucket=bucket)

    handler.handler(
        event(
            "DeleteBucketPublicAccessBlock", {"bucketName": bucket}, event_id="evt-42"
        )
    )

    line = json.loads(capsys.readouterr().out.strip())
    assert line["rule"] == "fix_public_access_block"
    assert line["correlation_id"] == "evt-42"
    (message,) = receive()
    assert "evt-42" in message["Body"] and bucket in message["Body"]


def test_an_already_compliant_bucket_notifies_nothing(cloud, monkeypatch, capsys):
    topic = setup(monkeypatch, cloud)
    receive = inbox(topic)
    bucket = f"{PREFIX}frontend-123456789012"
    boto3.client("s3").create_bucket(Bucket=bucket)
    boto3.client("s3").put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
            f: True
            for f in (
                "BlockPublicAcls",
                "IgnorePublicAcls",
                "BlockPublicPolicy",
                "RestrictPublicBuckets",
            )
        },
    )

    handler.handler(event("PutBucketPublicAccessBlock", {"bucketName": bucket}))

    assert capsys.readouterr().out == ""
    assert receive() == []
