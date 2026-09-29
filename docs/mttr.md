# Results

Time to remediate, loop safety and coverage, measured against the live environment on 2026-09-28 in `us-east-1`. Every number below comes from two records: the chaos scripts' `chaos/results.log` and the remediation Lambda's CloudWatch log group `/aws/lambda/self-healing-aws-infra-remediate`.

## How it is measured

Each chaos script (`chaos/break-*.sh`) checks the resource is compliant, records a start time, violates it with a real API call, then polls the resource's real state once a second until it is compliant again. It prints one line per run to `chaos/results.log` and exits non-zero on a timeout.

Two clocks are used, deliberately:

| Clock | Where it comes from | Used for |
|---|---|---|
| **T0** | The CloudTrail `eventTime` of the violating call, carried in the event the Lambda receives | The start of the headline measurement |
| **T2** | The moment the Lambda's fix call returns, written into its structured log line. The Lambda does not re-read the resource afterwards | The end of the headline measurement |
| `seconds` | The script's own `$SECONDS` counter, from just after the violating call until it sees the resource compliant | A cross-check from outside AWS |

The headline figure is T2 minus T0. It excludes the time the script spends issuing the API call, and it is entirely AWS-side, so it does not depend on the machine running the script. Runs were spaced 15 seconds apart so the events from one run's fix had settled before the next violation.

## S3-1: Block Public Access removed (headline)

Ten runs against the real site bucket, `self-healing-aws-infra-frontend-<account>`.

| Statistic | T2 minus T0 |
|---|---|
| p50 | 8.1 s |
| p95 | 11.6 s |
| max | 11.6 s |
| min | 5.4 s |

Sorted per-run values: 5.4, 6.5, 7.1, 7.6, 8.1, 8.2, 9.0, 10.8, 11.5, 11.6 seconds.

The script-side `seconds` for the same ten runs were 11, 9, 9, 6, 9, 11, 8, 11, 9 and 6. With ten samples the p95 is effectively the maximum, so the honest statement is "under 12 seconds at p95 over 10 runs".

The first run included a Lambda cold start (685 ms of initialisation, 1,502 ms billed) and is part of the sample. Most of the elapsed time is the delivery of the CloudTrail event to EventBridge, not the fix: the Lambda's billed duration for a fix was 0.5 to 1.0 seconds when warm.

## The other classes

| Rule | Runs | T2 minus T0 | Result |
|---|---|---|---|
| SG-1: port 22 open to `0.0.0.0/0` on the app security group | 5 | 3.1, 3.8, 4.7, 4.7, 5.9 s (median 4.7 s, max 5.9 s) | Verified |
| EC2-1: instance metadata service downgraded off IMDSv2 | 1 | 3.9 s | Verified |
| CT-1: CloudTrail logging stopped | 1 | 3.4 s | Verified |
| RDS-1: database made publicly accessible | 1 | none | Not verified, see below |

"Verified" means the chaos script polled the resource's real state and saw it compliant again, and the Lambda logged exactly one remediation for the violating call. Classes run fewer than ten times are not given percentiles.

## Loop safety

Across the 17 remediation runs that succeeded (10 S3-1, 5 SG-1, 1 EC2-1, 1 CT-1), the Lambda wrote **17 structured log lines with 17 distinct correlation IDs**, so no violating call was remediated twice. The correlation ID is the CloudTrail `eventID` of the violating call.

Each fix is itself an API write, so CloudTrail records it and EventBridge delivers it back to the Lambda. Those events were received and skipped as exempt in 2 to 3 milliseconds each, without a log line, because their actor is the Lambda's own role. The check the Lambda applies is:

1. Skip any event whose `userIdentity.sessionContext.sessionIssuer.arn` is the Lambda's role or the CI pipeline's role.
2. Otherwise re-read the resource's real state and do nothing if it is already compliant.

The second check also makes the function safe under EventBridge's at-least-once, asynchronous delivery.

To reproduce the count, run this over the window of your runs:

```
fields @timestamp, correlation_id
| filter ispresent(correlation_id)
| stats count() as fixes by correlation_id
| sort fixes desc
```

Every row should show `fixes = 1`.

## Notification

A confirmed SNS email subscription delivered the alert for a further S3-1 run (not part of the ten above). The message names the rule, the API call, the actor's ARN, the action taken, T0, T2 and the correlation ID, matching the Lambda's log line for that run. The earlier runs happened before the subscription was confirmed, so their alerts were published but not delivered; the notification is proven end to end for one run.

## Cost

See [cost.md](cost.md): about $0.0000025 per incident, from the billed durations of the 41 Lambda invocations in the measured window.

## Known limit: RDS-1

The RDS-1 run shows `outcome=remediated` in `chaos/results.log`, but it is not a real remediation, and it is excluded from every number above.

`ModifyDBInstance` returns immediately and RDS applies the change in the background. CloudTrail records the call, and the event reached the Lambda while `describe-db-instances` still reported `PubliclyAccessible=false`. The Lambda re-read the state, found it compliant and correctly did nothing. About 45 seconds later the instance became publicly accessible, and because the change had already been recorded there was no further event to react to. The chaos script's own compliance check made the same read and passed prematurely, after 2 seconds.

The rule and its unit tests exist and are correct for a database whose state has already changed, but against a live instance it does not close the loop. Handling it would mean acting on the request's `publiclyAccessible` parameter rather than the current state, and retrying while the instance is `modifying`. RDS is therefore not counted among the verified classes.

## AWS Config as an independent detector

Config's managed rules evaluated the same violations without being wired to the Lambda. In the observed runs the S3, EC2 and security-group rules flipped to `NON_COMPLIANT` after roughly 60 to 70 seconds, and the RDS and CloudTrail rules had not changed within about three minutes. The event path remediated S3-1 in a median of 8.1 seconds. Config is kept as a detection-only record, and its slower evaluation is why it is not the trigger.

## Conditions

- One AWS account, one region, one environment. The violating calls were made from a CLI user's credentials.
- The environment during the runs had one NAT Gateway and a single-AZ database with no backups. The event, Lambda and SNS path does not depend on either setting.
- The fix's own follow-up events are included in the invocation counts used for cost, and excluded from the incident counts.
