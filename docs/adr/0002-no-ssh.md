# ADR-0002: No SSH, Session Manager only

Status: Accepted

## Context

The application instances run in private subnets and are administered rarely: to read a log, inspect a release, or debug a failing deploy. Operators still need a shell when that happens, and the deploy pipeline needs to run commands on the instances.

## Decision

Instances have no key pair, run nothing that listens for administrative logins, and no security group in the environment allows port 22. Shell access and remote commands go through AWS Systems Manager.

The instance role carries the `AmazonSSMManagedInstanceCore` policy. The SSM agent, preinstalled on Amazon Linux 2023, connects outbound to the service through the NAT Gateway, so no inbound connection is ever needed. Operators open a shell with `aws ssm start-session --target <instance-id>`.

## Consequences

- There is no inbound administrative path to the instances: no open port, no bastion host, and no key to lose or rotate.
- Every session and every command is tied to an IAM identity and recorded in CloudTrail.
- Access is granted and revoked in IAM instead of by distributing keys.
- An instance must have outbound HTTPS to the SSM service, which the NAT Gateway provides. An instance that loses egress cannot be reached.
- An ingress rule on port 22 anywhere in the environment contradicts this decision, so the remediation loop treats it as a violation.
