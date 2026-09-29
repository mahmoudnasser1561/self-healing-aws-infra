# Cost

Two different costs matter here: what one remediation costs (measured), and what the environment costs while it is up (estimated from list prices). The environment is built to be created and destroyed by the pipeline on demand, so the second number applies only for the hours it exists.

## Cost per incident (measured)

Source: the CloudWatch Logs `REPORT` lines of the remediation Lambda for every invocation between 10:17 and 10:26 UTC on 2026-09-28, the window of the S3-1, SG-1, EC2-1, CT-1 and RDS-1 chaos runs.

| Quantity | Value |
|---|---|
| Lambda invocations in the window | 41 |
| Of which fixed a violation | 17 |
| Of which were no-ops (the Lambda's own follow-up events, skipped as exempt, and the RDS-1 event) | 24 |
| Total billed duration | 12,265 ms |
| Memory | 128 MB (0.125 GB) |
| Cold starts | 1 (685 ms of billed initialisation) |

Published `us-east-1` Lambda prices for x86: $0.0000166667 per GB-second and $0.20 per million requests.

```
compute   12.265 s x 0.125 GB = 1.533 GB-s
          1.533 GB-s x $0.0000166667             = $0.0000256
requests  41 x $0.20 / 1,000,000                 = $0.0000082
Lambda total                                     = $0.0000338

per incident   $0.0000338 / 17                   = $0.0000020
SNS publish    1 x $0.50 / 1,000,000             = $0.0000005
                                                   ---------
per incident                                     ~ $0.0000025
```

The figure charges every invocation in the window, including the 24 that did nothing, to the 17 incidents that caused them. The billed duration of an individual fix was 466 ms to 1,028 ms when warm and 1,502 ms on the cold start.

Not in the figure, because they cost nothing at this volume:

- EventBridge: events from AWS services on the default bus are free.
- CloudTrail: the first copy of management events in a region is free.
- Email delivery: the first 1,000 SNS email deliveries each month are free.

Not in the figure, because they are standing costs rather than costs of an incident: the AWS Config recorder and rule evaluations, and the CloudWatch Logs retained for seven days.

## Cost while the environment is up (estimate)

These are list-price estimates in `us-east-1`, not billing data. They exist to show where the money goes; check current prices before relying on them.

| Component | Basis | About, per hour |
|---|---|---|
| NAT Gateways | 2 × $0.045, plus $0.045 per GB processed | $0.090 |
| Application Load Balancer | $0.0225 plus load-balancer capacity units | $0.023 |
| EC2 | 2 × `t3.micro` at $0.0104 | $0.021 |
| RDS PostgreSQL | `db.t4g.micro` Multi-AZ, about 2 × $0.016, plus 20 GB gp3 storage in two zones | $0.038 |
| WAF | one web ACL and two managed rule groups, about $7 per month | $0.010 |
| Public IPv4 addresses | about 4 × $0.005 | $0.020 |
| CloudFront, S3, CloudWatch, Config, Lambda, SNS | usage-based, small at this scale | under $0.01 |
| **Total** | | **about $0.20** |

The two NAT Gateways are the largest fixed line, which is the trade-off recorded in [ADR-0001](adr/0001-nat-gateway-egress.md): egress stays inside each availability zone, at an hourly price for each. The pipeline's apply took about 6.5 minutes, so a working session of an hour or two costs well under a dollar; leaving the environment up for a month would cost roughly $145.

## Keeping it cheap

- `apply` and `destroy` are both pipeline jobs behind an approval, so the environment exists only when someone approves it.
- Every log group and log bucket expires its contents after seven days.
- The remediation Lambda is 128 MB with a 30 second timeout, and the longest billed duration observed was 1.5 seconds, on a cold start.
- Config records only the four resource types the rules evaluate: S3 buckets, security groups, EC2 instances and RDS instances.
