# ADR-0001: NAT Gateways provide private egress

Status: Accepted

## Context

The application instances run in private subnets with no public IP addresses and no SSH access. They still need outbound connectivity to work:

- Session Manager, which is how operators reach the instances
- Operating-system packages and Python dependencies at boot and at deploy time
- The release bucket in S3, where the deploy pipeline publishes each build
- The Secrets Manager API, to read the database credentials

The data tier needs none of this and should not be able to reach the internet at all.

## Decision

Each availability zone gets its own NAT Gateway with its own Elastic IP, placed in that zone's public subnet. Each private app route table sends `0.0.0.0/0` to the NAT Gateway in its own zone. The data tier's route table has no default route.

There are no VPC endpoints. Every outbound destination, AWS service or public repository, is reached through the same NAT path.

## Consequences

- One mechanism covers every destination the instances need, including public package repositories that no AWS endpoint serves.
- Zones fail independently. If one zone's NAT Gateway is lost, only the instances in that zone lose egress, and egress traffic never crosses zones, so it carries no cross-zone transfer charge.
- The NAT Gateways are the largest fixed cost in the network tier: an hourly charge each plus a per-GB processing charge. The environment is built to be created and destroyed on demand by the pipeline, so they run only while it is up.
- The app tier's security group allows outbound TCP 443 to any address, because the NAT path offers no narrower destination list. Egress control at the destination level is not part of this design.
- The data tier is isolated by routing as well as by its security group: even a misconfigured rule cannot give it a path out.
