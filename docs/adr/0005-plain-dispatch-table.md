# ADR-0005: One handler and a dispatch table

Status: Accepted

## Context

The remediation layer has to cover a handful of violation classes today and stay easy to extend and to audit. Its code runs with permission to change infrastructure, so how easily it can be read and tested is a security property.

## Decision

The Lambda is two Python files. `handler.py` is the pipeline and `rules.py` holds the rules.

`rules.py` has one function per violation class and a dictionary from CloudTrail API call name to function:

```python
RULES = {
    "DeleteBucketPublicAccessBlock": fix_public_access_block,
    "PutBucketPublicAccessBlock": fix_public_access_block,
    "AuthorizeSecurityGroupIngress": fix_open_ingress,
    "ModifyDBInstance": fix_public_rds,
    "ModifyInstanceMetadataOptions": fix_imdsv2,
    "StopLogging": fix_stopped_trail,
}
```

A rule function takes the CloudTrail `detail` object and returns a short description of what it changed, or `None` when it did nothing. It checks that the resource belongs to this project, re-reads the resource, applies the smallest fix and returns. The handler is the same for every rule: look up the API call, skip events from the exempt roles, call the rule, and on a result publish one SNS message and write one structured log line whose `correlation_id` is the CloudTrail `eventID`.

Adding a rule is four changes: a function and a dictionary entry in `rules.py`, a unit test, the IAM statement it needs in `modules/remediation/lambda.tf`, and the API's service in `api_sources` in `modules/detection/events.tf` if it is a new one.

## Consequences

- The whole decision path fits on one screen, and every rule has its own tests against fakes of the service it changes.
- Scope is checked inside each rule (a name prefix or the `Project` tag), so a rule cannot act on a resource outside the project even if the event names one.
- The table is the registry: there is no discovery step and no layer between the handler and a rule. A rule reads the resource before it acts and does not re-read it afterwards; the chaos scripts confirm each fix independently, from outside AWS's event path, by polling the resource's real state.
- A rule is keyed on a single API call name. A violation that can only be recognised from a combination of events needs a different mechanism.
- The Lambda's IAM policy lists each action explicitly, so extending the code and extending its permissions are reviewed together.
