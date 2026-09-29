# ADR-0004: Remediation is driven by API events, and AWS Config only detects

Status: Accepted

## Context

A misconfiguration such as a public bucket or a world-open security group should be reverted while it is still an incident, not at the next compliance sweep. CloudTrail records every management API call and delivers it to the EventBridge default bus within seconds. AWS Config evaluates resources on its own schedule; in the runs recorded in [mttr.md](../mttr.md) its rules took about a minute to flag the S3, EC2 and security-group violations, and had not flagged the RDS and CloudTrail ones after three minutes.

## Decision

One EventBridge rule, `self-healing-aws-infra-api-writes`, matches every write call (`readOnly = false`) from S3, EC2, RDS and CloudTrail and invokes the remediation Lambda directly. The Lambda decides from the API call's name whether the call could have created a violation, re-reads the resource, and fixes it only if it is still violated.

The rule matches on the event's top-level `source` field, not on `detail.eventSource`, because that is how CloudTrail events are presented on the bus. CloudTrail events carry no `resources` list, so the Lambda reads the resource identifier from `requestParameters`, whose field name and nesting differ by API.

The environment creates its own trail (`create_trail`, on by default) so the path works in an account that has none. AWS Config runs alongside with six managed rules, an independent record of compliance. It is detection only and is not connected to the Lambda: its compliance-change events have a different shape from API events, and the API path already reacts faster.

## Consequences

- Remediation takes seconds: a median of 8.1 s for S3-1 over ten runs, dominated by event delivery rather than by the fix.
- EventBridge invokes the Lambda asynchronously with at-least-once delivery, so every rule must be idempotent. Each one re-reads real state and does nothing if the resource is already compliant.
- The Lambda's own fixes are API writes that come back through the same rule. They are recognised by their actor and skipped, so a fix cannot retrigger itself.
- A violation that is not the result of one of the listed API calls is not caught by this path. Config records it, but does not fix it.
- A change that a service applies asynchronously can be reported by CloudTrail before it is visible in the resource's state. The RDS rule is affected by this, see [mttr.md](../mttr.md#known-limit-rds-1).
- The trail and the Config recorder are part of the environment and are created and destroyed with it.
