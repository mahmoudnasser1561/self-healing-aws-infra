import json
import os
from datetime import datetime, timezone

import boto3

import rules

sns = boto3.client("sns")


def exempt_roles():
    return {arn for arn in os.environ.get("EXEMPT_ROLE_ARNS", "").split(",") if arn}


def actor_role(detail):
    identity = detail.get("userIdentity", {})
    issuer = identity.get("sessionContext", {}).get("sessionIssuer", {})
    return issuer.get("arn", "")


def notify(rule_name, resource_detail, result, t0, t2):
    subject = f"[self-healing] {rule_name}"[:100]
    message = "\n".join(
        [
            f"rule: {rule_name}",
            f"event: {resource_detail['eventName']}",
            f"actor: {resource_detail.get('userIdentity', {}).get('arn', 'unknown')}",
            f"action: {result}",
            f"t0: {t0}",
            f"t2: {t2}",
            f"correlation_id: {resource_detail.get('eventID', '')}",
        ]
    )
    sns.publish(TopicArn=os.environ["TOPIC_ARN"], Subject=subject, Message=message)


def handler(event, context=None):
    detail = event["detail"]
    fn = rules.RULES.get(detail["eventName"])
    if fn is None:
        return

    if actor_role(detail) in exempt_roles():
        return

    result = fn(detail)
    if result is None:
        return

    t0 = detail["eventTime"]
    t2 = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    notify(fn.__name__, detail, result, t0, t2)
    print(
        json.dumps(
            {
                "rule": fn.__name__,
                "event": detail["eventName"],
                "action": result,
                "t0": t0,
                "t2": t2,
                "correlation_id": detail.get("eventID", ""),
            }
        )
    )
