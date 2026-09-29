# Infra Reference

How the Terraform is organised, what each module builds, and what it hands to the next one. `envs/dev` is applied by the pipeline; `bootstrap/` is applied once, locally.

## Repository layout

| Path | Purpose |
|---|---|
| `bootstrap/` | State bucket, GitHub OIDC provider, and the CI role with its policies. Applied once from a workstation. |
| `envs/dev/` | The deployable environment: provider, backend, and the module calls that wire everything together. |
| `modules/` | One module per component. Each has `main.tf`, `variables.tf` and `outputs.tf`; larger ones split resources by concern into further files. |
| `backend` branch | The Flask API, its tests and its pipeline, on a separate history that shares no commits with `main`. |

`envs/dev/main.tf` is the only place one module's outputs become another's inputs.

## Modules

| Module | Creates | Inputs | Outputs |
|---|---|---|---|
| `networking` | VPC, six subnets, internet gateway, NAT Gateways with Elastic IPs, route tables, VPC flow logs with their log group and delivery role | `project` | `vpc_id`, `public_subnet_ids`, `app_subnet_ids`, `data_subnet_ids` |
| `security` | Load-balancer, app-tier and data-tier security groups and their rules | `project`, `vpc_id` | `alb_sg_id`, `app_sg_id`, `data_sg_id` |
| `data` | DB subnet group, RDS Postgres instance with an RDS-managed master secret | `project`, `data_subnet_ids`, `data_sg_id` | `db_address`, `db_port`, `db_secret_arn` |
| `backend` | Application load balancer, launch template, Auto Scaling group with a scaling policy, instance role and profile, releases bucket, application log group, load balancer access-log bucket | `project`, `vpc_id`, `public_subnet_ids`, `app_subnet_ids`, `alb_sg_id`, `app_sg_id`, `db_address`, `db_secret_arn` | `alb_dns_name`, `asg_name`, `releases_bucket`, `alb_logs_bucket` |
| `detection` | CloudTrail trail with its log bucket, the EventBridge rule that matches write API calls, the AWS Config recorder with its delivery channel, bucket and service-linked role, and six AWS-managed Config rules | `project`, `create_trail` | `api_writes_rule`, `config_rule_names`, `config_bucket` |
| `remediation` | Remediation Lambda with its role and log group, alert SNS topic with an optional email subscription, and the permission and target that connect each supplied rule to the Lambda | `project`, `alert_email`, `trigger_rules` | `remediate_function`, `alerts_topic_arn` |
| `frontend` | Private S3 bucket for the React build, CloudFront distribution with origin access control and access logging, web ACL with its log group and logging configuration, access-log bucket | `project`, `alb_dns_name` | `cloudfront_domain`, `distribution_id`, `frontend_bucket`, `cloudfront_logs_bucket`, `waf_log_group` |

Dependencies run one way: `networking` → `security` → `data`, and `backend` takes the outputs of all three. `frontend` takes the load balancer's address from `backend`. `remediation` receives the EventBridge rule from `detection` through `envs/dev/main.tf`, so what is watched and what reacts to it are separate modules. The subnet outputs are lists with one entry per availability zone, index 0 in the first zone and index 1 in the second.

## Networking

### Address plan

The VPC is `10.0.0.0/16` across two availability zones, chosen at plan time from the zones available in the region.

| Tier | AZ a | AZ b |
|---|---|---|
| Public | `10.0.0.0/24` | `10.0.1.0/24` |
| Private app | `10.0.10.0/24` | `10.0.11.0/24` |
| Private data | `10.0.20.0/24` | `10.0.21.0/24` |

### Tiers and routing

| Tier | Holds | Default route |
|---|---|---|
| Public | Load balancer, NAT Gateways | Internet gateway |
| Private app | Application instances | NAT Gateway in the same AZ |
| Private data | Database | None — local traffic only |

There is one route table shared by the public subnets, one route table per AZ for the app subnets, and one route table shared by the data subnets. No subnet assigns public IP addresses to what launches in it; the load balancer and NAT Gateways get their public addresses from AWS and their Elastic IPs.

### Egress

Each AZ has its own NAT Gateway with its own Elastic IP, placed in that AZ's public subnet. Instances in the private app subnets reach Session Manager, package repositories, the release bucket in S3, and the Secrets Manager API through the NAT Gateway in their own AZ. The data tier has no route out. There are no VPC endpoints. See [ADR-0001](adr/0001-nat-gateway-egress.md).

### Network ACLs

Network ACLs stay at the VPC default on every tier. Security groups are the access control.

### Flow logs

Flow logs capture all traffic for the VPC with a 60-second aggregation interval. They are written to the CloudWatch log group `/self-healing-aws-infra/vpc-flow-logs`, which keeps seven days of history. The delivery role, `self-healing-aws-infra-vpc-flow-logs`, can only be assumed by the VPC Flow Logs service on behalf of this account, and can only write to that log group.

### Tags

The provider applies `Project`, `Environment` and `ManagedBy` to every resource. Each resource also carries a `Name`, and each subnet a `Tier` of `public`, `app` or `data`.

## Security groups

Every security group lives in the `security` module, so one file set shows who can reach what. Rules are separate resources that reference other groups by ID, not by address range. Egress is explicit: a group has no outbound access that is not listed here.

| Group | Direction | Port | Peer |
|---|---|---|---|
| Load balancer | Ingress | TCP 80 | CloudFront's origin-facing managed prefix list |
| Load balancer | Egress | TCP 8000 | App-tier group |
| App tier | Ingress | TCP 8000 | Load-balancer group |
| App tier | Egress | TCP 5432 | Data-tier group |
| App tier | Egress | TCP 443 | `0.0.0.0/0`, through the NAT Gateway |
| Data tier | Ingress | TCP 5432 | App-tier group |

The data-tier group has no egress rules; responses to accepted connections need none. Port 22 appears in no rule anywhere in the environment.

## Data

The database is RDS for PostgreSQL 16 in the private data subnets, in a subnet group that spans both data subnets. It runs as a Multi-AZ instance (`db.t4g.micro`, 20 GB gp3): a synchronous standby in the second zone takes over automatically, and the endpoint name does not change across a failover. Storage is encrypted with the AWS-managed RDS key, and automated backups are kept for seven days.

The database is named `app` and the master user is `dbadmin`. The password is generated and rotated by RDS and stored in an RDS-managed Secrets Manager secret (`rds!db-…`). It never appears in Terraform code, user-data or application configuration. The module exposes only the secret's ARN.

The instance is not publicly accessible. The only path to it is TCP 5432 from the app-tier security group. Final snapshots and deletion protection are off so the environment tears down cleanly. See [ADR-0006](adr/0006-data-tier-design.md).

Terraform state records the secret ARN and other sensitive values. That is why access to the state bucket is restricted to the account and the CI role, and not only encrypted.

## Backend

The API tier is one module, `backend`: an application load balancer in front of an Auto Scaling group whose instances run the Flask API. The application source lives on the `backend` branch, not in `main`.

### Load balancer

An internet-facing application load balancer in the two public subnets, attached to the load-balancer security group, dropping invalid HTTP headers. One HTTP listener on port 80 forwards every request to a target group that sends it to port 8000 on the instances. TLS ends at CloudFront, not here.

The target group's health check is `GET /api/health`, expecting `200`, every 15 seconds with a 5-second timeout. An instance is healthy after two passes and unhealthy after three failures, and is given 30 seconds to drain when it leaves.

### Auto Scaling group

| Setting | Value |
|---|---|
| Name | `self-healing-aws-infra-app` |
| Size | 2 desired, 2 minimum, 3 maximum, spread across both private app subnets |
| Health check | Load balancer, with a 15-minute grace period so a new instance can fetch its release before it is judged |
| Scaling | Target tracking on average CPU at 50% |
| Tags on instances | `Name` and `Project`, which the deploy pipeline uses to find them |

### Instances

The launch template starts the latest Amazon Linux 2023 image on `t3.micro`. The instance metadata service requires session tokens (IMDSv2), the root volume is an encrypted 8 GB gp3 disk, there is no key pair, and the instance runs under the app security group and the instance profile below. Its user-data does everything else: it installs Python 3.11 and the CloudWatch agent, creates an unprivileged `app` user, writes `/etc/app.env`, installs the deploy script and the service unit, waits for the first release, and finally starts the log agent.

On an instance the application lives in `/opt/app/src` with its virtualenv in `/opt/app/venv`, and runs as the `app` systemd service (`gunicorn -c gunicorn.conf.py wsgi:app`, port 8000), restarted automatically if it stops. `/etc/app.env` holds the only configuration: `DB_HOST`, `DB_SECRET_ARN`, `AWS_REGION` and `RELEASE_BUCKET`. The database name (`app`), port and SSL mode are the application's defaults. It contains no password: each gunicorn worker opens one database connection the first time it needs it, reading the credentials from Secrets Manager at that moment, and keeps using it. If the database restarts or fails over, the next request after the drop fails and the one after it opens a new connection.

### Instance role

The role `self-healing-aws-infra-app` carries the AWS-managed `AmazonSSMManagedInstanceCore` and `CloudWatchAgentServerPolicy` policies, plus an inline policy that allows exactly three more things: reading the database secret, listing the releases bucket and reading objects from it.

### Releases bucket

`self-healing-aws-infra-app-releases-<account-id>` is private, versioned and encrypted, with all public access blocked. The pipeline writes `releases/<commit-sha>.tar.gz` and, once a release has deployed to every instance, copies it to `releases/latest.tar.gz`; each tarball holds the application code, `gunicorn.conf.py`, `requirements.txt` and a `VERSION` file containing the commit sha. Instances only read from it.

### Logs

gunicorn writes `access.log` and `error.log` under `/var/log/app`. The CloudWatch agent ships them to the log group `/self-healing-aws-infra/app`, one stream per instance and file, and the group keeps seven days.

The load balancer also writes its access logs to the private bucket `self-healing-aws-infra-alb-logs-<account-id>`, under `alb/`. The bucket is encrypted with S3-managed keys, blocks all public access, and expires objects after seven days. Its policy lets only the regional Elastic Load Balancing service account write into the load balancer's own log path.

### Access

There is no SSH. Operators open a shell with `aws ssm start-session --target <instance-id>`, and the deploy pipeline reaches the instances through the same service. See [ADR-0002](adr/0002-no-ssh.md).

### The application

The API is a small to-do list stored in one `todos` table (`id`, `title`, `created_at`), created from `app/schema.sql` the first time a worker connects. There is one shared list and no authentication.

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | A round trip to the database: returns the database clock, the number of todos and the release version, or `503` when the database is unreachable |
| `GET /api/todos` | All todos, newest first |
| `POST /api/todos` | Create a todo from `{"title": "..."}`; the title must be 1 to 200 characters, otherwise `400` |
| `DELETE /api/todos/<id>` | Delete a todo; returns `204` whether or not it existed |

The application is a Flask factory (`create_app`) with its configuration in `config.py`, the database connection in `db.py` and the routes in `routes.py`.

## Frontend

The web tier is one module, `frontend`: a private S3 bucket holding the React build and a CloudFront distribution in front of it, with a web ACL attached to the distribution. CloudFront is the only public entry point to the whole system.

### Bucket

`self-healing-aws-infra-frontend-<account-id>` is private and encrypted, with all four public-access blocks on. Its policy allows exactly one thing: `s3:GetObject` for the CloudFront service, and only on behalf of this distribution. Nothing else, and nobody else, can read it.

### Distribution

| Setting | Value |
|---|---|
| Origins | The S3 bucket, reached through origin access control (signed requests), and the application load balancer, reached over HTTP on port 80 |
| Default behaviour | The React app from the bucket, served over HTTPS (HTTP is redirected), compressed, using the AWS-managed caching-optimised policy |
| `/api/*` | Forwarded to the load balancer with every method allowed, no caching, and all viewer headers and query strings passed through except `Host` |
| Root object | `index.html` |
| Certificate | CloudFront's default `*.cloudfront.net` certificate; see [ADR-0003](adr/0003-tls-via-cloudfront.md) |
| Coverage | IPv6 enabled, price class 100 (North America and Europe edge locations) |

The browser sees one domain for both the app and the API, so the API needs no CORS configuration. The cache and request policies are looked up by their AWS-managed names rather than by ID. The React source and its pipeline live on the `frontend` branch; see [ADR-0007](adr/0007-frontend-delivery.md).

### Web ACL

A WAF web ACL with scope `CLOUDFRONT` is attached to the distribution, so requests are inspected at the edge before they reach the bucket or the load balancer. Its default action is allow, and it carries two AWS-managed rule groups:

| Priority | Rule group | Covers |
|---|---|---|
| 1 | `AWSManagedRulesCommonRuleSet` | Cross-site scripting, local and remote file inclusion, restricted file extensions, oversized requests, requests with no user agent, known bad bots and requests for the instance metadata address |
| 2 | `AWSManagedRulesKnownBadInputsRuleSet` | Log4j and Java deserialisation payloads, requests for `localhost` as the host, and paths that are known to be exploitable |

The rule groups run with their own actions, so a matching request is blocked with a 403 at the edge. This web ACL has no rules of its own, and SQL injection has its own managed group that is not attached. Each rule and the web ACL publish CloudWatch metrics and keep sampled requests.

Every request the web ACL inspects is logged in full to the log group `aws-waf-logs-self-healing-aws-infra`, with seven days of retention. WAF requires that prefix on a log group it writes to, and it adds the log group's resource policy itself. CloudFront web ACLs can only be created in `us-east-1`, so the environment's region has to stay `us-east-1`; the module uses the default provider and has no region alias.

### Access logs

CloudFront writes its standard access logs to the private bucket `self-healing-aws-infra-frontend-logs-<account-id>`, under `cloudfront/`, without cookies. The bucket is encrypted with S3-managed keys, blocks all public access, and expires objects after seven days. CloudFront delivers through a bucket ACL, so this bucket keeps ACLs enabled with bucket-owner-preferred ownership; CloudFront adds its own delivery grant when the logging is configured. The bucket is separate from the site bucket, which enforces bucket-owner ownership and has no ACLs.

### Load balancer access

The load balancer's security group accepts TCP 80 only from CloudFront's origin-facing managed prefix list. A request sent straight to the load balancer's address is refused, so every request reaches the API through CloudFront.

## Remediation

Two modules build the self-healing loop. `detection` decides what is watched and `remediation` decides what reacts, and `envs/dev/main.tf` connects them by passing the EventBridge rule as `trigger_rules`.

### What is watched

| Resource | Detail |
|---|---|
| Trail `self-healing-aws-infra` | Management events, log-file validation on, in a private bucket that expires objects after seven days. Created only when `create_trail` is true (the default), so the environment works in an account that has no trail |
| EventBridge rule `self-healing-aws-infra-api-writes` | On the default bus, matches CloudTrail events (`detail-type` "AWS API Call via CloudTrail") whose `source` is `aws.s3`, `aws.ec2`, `aws.rds` or `aws.cloudtrail` and whose `detail.readOnly` is false |
| AWS Config | A recorder for S3 buckets, security groups, EC2 instances and RDS instances, and six AWS-managed rules: `s3-bucket-level-public-access-prohibited`, `restricted-ssh`, `restricted-common-ports` (22, 3389, 5432), `rds-instance-public-access-check`, `ec2-imdsv2-check` and `cloudtrail-enabled`. Detection only |

### What reacts

The Lambda `self-healing-aws-infra-remediate` (Python 3.12, 128 MB, 30 s, seven days of logs) is the target of the rule. Its source is `lambdas/remediate`: `handler.py` is the pipeline and `rules.py` holds one function per violation class and the table that maps a CloudTrail API call name to it ([ADR-0005](adr/0005-plain-dispatch-table.md)).

For every event the function follows the same steps: look the API call up in the table, skip the event if its actor is an exempt role, confirm the resource belongs to the project, re-read the resource's real state, do nothing if it is already compliant, apply the smallest fix, publish to SNS and write one structured log line. The log line has the fields `rule`, `event`, `action`, `t0` (the CloudTrail `eventTime`), `t2` (when the fix returned) and `correlation_id` (the CloudTrail `eventID`).

| Setting | Value |
|---|---|
| Rules | S3-1 Block Public Access, SG-1 world-open ingress, RDS-1 public database, EC2-1 IMDSv2, CT-1 trail logging. See the [README](../README.md#the-self-healing-loop) for the calls and fixes |
| Scope | S3 buckets, databases and trails whose names start with `self-healing-aws-infra`, and security groups and instances tagged `Project=self-healing-aws-infra` |
| Exempt roles | The function's own role and the pipeline's role `self-healing-aws-infra-github-actions`, passed in `EXEMPT_ROLE_ARNS` and compared with the event's `sessionContext.sessionIssuer.arn` |
| Invocation | Asynchronous from EventBridge, at least once. The function re-reads state before acting, so a repeated delivery does nothing |
| Notification | An SNS topic `self-healing-aws-infra-alerts` with an email subscription. The address comes from the repository variable `ALERT_EMAIL` and is never stored in the repository. The subscription must be confirmed once from the email AWS sends |

### Function permissions

The role `self-healing-aws-infra-remediate` allows only these actions:

| Purpose | Actions | Limited to |
|---|---|---|
| S3-1 | `s3:GetBucketPublicAccessBlock`, `s3:PutBucketPublicAccessBlock` | Buckets named `self-healing-aws-infra-*` |
| SG-1 | `ec2:DescribeSecurityGroups`, `ec2:DescribeSecurityGroupRules`, `ec2:RevokeSecurityGroupIngress` | The deployment region; revoke on this account's security groups |
| EC2-1 | `ec2:DescribeInstances`, `ec2:ModifyInstanceMetadataOptions` | The deployment region |
| RDS-1 | `rds:DescribeDBInstances`, `rds:ModifyDBInstance` | The deployment region |
| CT-1 | `cloudtrail:GetTrailStatus`, `cloudtrail:StartLogging` | Trails named `self-healing-aws-infra*` |
| Notification | `sns:Publish` | The alerts topic |
| Logging | `logs:CreateLogStream`, `logs:PutLogEvents` | Its own log group |

The function's code additionally checks the project name prefix or tag before it acts, so the permission scope and the code scope both have to allow a change.

### Limits

The API path reacts to calls it has a rule for, and a change that a service applies asynchronously can be visible in CloudTrail before it is visible in the resource. The RDS rule is affected by this; see [mttr.md](mttr.md#known-limit-rds-1). Design rationale: [ADR-0004](adr/0004-event-driven-remediation.md).

## Deployment pipeline

`.github/workflows/terraform.yml` runs when `envs/` or `modules/` change on `main`, or on manual dispatch. It has three jobs in sequence:

1. **plan** runs `terraform plan` and prints it in the job log. The alert address is passed in as `TF_VAR_alert_email` from the repository variable `ALERT_EMAIL`.
2. **apply** waits for reviewer approval on the `prod` environment, then runs `terraform apply`.
3. **destroy** waits for the same approval, then runs `terraform destroy` on the environment.

Only `main` can deploy. The jobs authenticate to AWS by exchanging the workflow's GitHub OIDC token for short-lived credentials; no AWS credentials are stored in GitHub.

### Backend pipeline

`.github/workflows/backend.yml` lives on the `backend` branch and runs for pushes and pull requests to it.

1. **test** runs `black --check`, `flake8` and `pytest` on Python 3.11.
2. **deploy-role-check** (pushes only) assumes the deploy role and prints its identity, confirming the OIDC login works.
3. **deploy** (pushes only, after the tests pass, and only when the repository variable `BACKEND_DEPLOY_ENABLED` is `true`) writes the commit sha to `VERSION`, packages the application, uploads `releases/<sha>.tar.gz`, and then runs `scripts/rollout.sh`, which sends the deploy command for that sha to the group's instances one at a time and fails the run if any instance does not succeed. Only after that does it copy the release to `releases/latest.tar.gz`.

![Backend release flow](diagrams/backend_release_flow.png)

Instances that start later, by scale-out or as replacements, run the same deploy script at boot with no argument, so they always start on `latest`.

![New and replacement instances](diagrams/backend_instance_boot.png)

See [ADR-0008](adr/0008-ssm-rolling-deploy-not-codedeploy.md).

### Frontend pipeline

`.github/workflows/frontend.yml` lives on the `frontend` branch and runs for pushes and pull requests to it.

1. **check** runs ESLint, the TypeScript type check, the tests and a production build.
2. **deploy-role-check** (pushes only) assumes the frontend deploy role and prints its identity, confirming the OIDC login works.
3. **deploy** (pushes only, after the checks pass, and only when the repository variable `FRONTEND_DEPLOY_ENABLED` is `true`) rebuilds the application, then runs `scripts/deploy.sh`, which syncs the build to the frontend bucket with `--delete`, finds the distribution by its comment, invalidates everything in CloudFront and waits for the invalidation to finish.

Without the invalidation CloudFront would keep serving the previous build, so the script waits for it before it reports success. See [ADR-0007](adr/0007-frontend-delivery.md).

## CI permissions

The role `self-healing-aws-infra-github-actions` can be assumed only by workflow runs on `main` or in the `prod` environment. Its permissions are customer-managed policies attached in `bootstrap/`:

| Policy | Grants |
|---|---|
| `networking` | The EC2 actions Terraform uses for VPCs, subnets, gateways, route tables, security groups and flow logs, limited to the deployment region |
| `data` | RDS management on this account and region, the calls RDS makes on the caller's behalf for its managed secret, and KMS grants only for AWS-service use |
| `platform` | IAM role and instance profile management restricted to names starting `self-healing-aws-infra-`, attaching only the SSM and CloudWatch agent managed policies, `iam:PassRole` limited to the service that receives the role, the service-linked roles that Auto Scaling and load balancing need, and log groups under `/self-healing-aws-infra/` |
| `backend` | Launch templates, load balancing and Auto Scaling in the deployment region, full access to the releases bucket and the load balancer logs bucket, the public Amazon Linux image parameters, and the SSM deploy path |
| `selfheal` | The remediation function, its EventBridge rule, the alert topic and the trail, each limited to names starting `self-healing-aws-infra-` in the deployment region, the AWS Config recorder, delivery channel and rules with their service-linked role and bucket, and the trail and Config buckets |
| `frontend` | CloudFront, the web ACL and its log group, the log-delivery calls WAF uses to write to it and the service-linked role for WAF logging, full access to the frontend bucket, and reading CloudFront's managed prefix list |

An explicit deny stops the role from modifying its own policies or trust. Each policy was checked against the role with the IAM policy simulator.

The backend pipeline uses a second, much narrower role, `self-healing-aws-infra-backend-deploy`, defined in `bootstrap/` as well. It can be assumed only by workflows on the `backend` branch. It can read and write the releases bucket but not delete from it, send the deploy command through SSM to instances tagged with this project, and run read-only checks on the rollout. It has no IAM, EC2 or database permissions, and no access to the Terraform state. Its permissions were checked with the IAM policy simulator, both for what it must be able to do and for what it must not.

The frontend pipeline has its own role in the same way, `self-healing-aws-infra-frontend-deploy`, assumable only by workflows on the `frontend` branch. It can write to and delete from the frontend bucket, create and read cache invalidations, and look up the distribution. It cannot change the bucket or the distribution, and it has no access to the releases bucket, the Terraform state, the instances, IAM or EC2.

