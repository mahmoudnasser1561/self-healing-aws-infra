# ADR-0006: Data tier design

Status: Accepted

## Context

The backend API needs a relational database that holds real state, so the health check exercises a genuine database round trip. The database must be unreachable from the internet, must survive the loss of an availability zone, and must not put a password in code, user-data or application configuration.

## Decision

**Placement and access.** RDS for PostgreSQL 16 runs in the private data subnets, in a DB subnet group spanning both zones. It is not publicly accessible. Its security group allows TCP 5432 from the app-tier security group and nothing else, and the data subnets have no route to the internet.

**Availability.** The instance is Multi-AZ: a synchronous standby in the second zone takes over automatically, and the endpoint name stays the same across a failover. Storage is encrypted with the AWS-managed RDS key. Automated backups are kept for seven days.

**Credentials.** RDS generates and rotates the master password and stores it in an RDS-managed Secrets Manager secret. Terraform holds only the secret's ARN. The application instance role is granted `secretsmanager:GetSecretValue` on that one secret, and the application reads it when it connects. The application authenticates as the master user.

**Lifecycle.** `skip_final_snapshot` is true and `deletion_protection` is false. The environment is created and destroyed by the pipeline, and a destroy must finish cleanly without a snapshot decision. Automated backups are deleted with the instance. A long-lived deployment would enable both settings.

## Consequences

- A database credential never exists in the repository, in Terraform code, or in a pipeline variable.
- Terraform state contains the secret ARN, the database endpoint and other sensitive values. The state bucket is therefore private, encrypted and readable only by the account and the CI role.
- Destroying the environment destroys the data. This is intended for a demonstration environment and is the reason the two lifecycle settings above would change in a long-lived one.
- A failover or restart drops the application's open connection for the time the standby takes to be promoted. The first request after the drop fails, and the next opens a new connection and reads the secret again, so the application recovers without intervention.
