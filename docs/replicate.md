# Replicate it

A complete walkthrough for building the environment in your own AWS account, running the chaos tests and tearing it down. Each step ends with a check. The condensed version is in the [README](../README.md#replicate-it).

The environment costs roughly $0.20 per hour while it is up ([cost.md](cost.md)). Plan to create it, run the tests and destroy it in one sitting.

## Prerequisites

| Need | Notes |
|---|---|
| An AWS account you can administer | The one-time bootstrap creates IAM roles and an OIDC provider, so use administrator credentials on your workstation |
| Region `us-east-1` | CloudFront web ACLs can only be created there, so the region is fixed |
| No existing AWS Config recorder in the region | An account allows one recorder per region. If yours has one, remove it first or expect the apply to fail creating `aws_config_configuration_recorder.main` with `MaxNumberOfConfigurationRecordersExceededException` |
| A GitHub account | The pipelines use GitHub Actions and GitHub's OIDC provider |
| Terraform 1.10 or later | The state backend uses S3 native locking (`use_lockfile`) |
| AWS CLI v2, GitHub CLI (`gh`), `git`, Python 3.12 | Python is only needed to run the unit tests |

Check your tools and identity:

```bash
terraform version | head -1
aws sts get-caller-identity
gh auth status
```

## 1. Fork and clone

```bash
gh repo fork mahmoudnasser1561/self-healing-aws-infra --clone
cd self-healing-aws-infra
```

Forks start with Actions disabled. Open the fork's **Actions** tab and choose to enable workflows.

Check: `git branch -a` lists `main`, `origin/backend` and `origin/frontend`. The API and the SPA live on those two branches.

## 2. Point the configuration at your account

Two values are specific to an account and repository: the numeric GitHub IDs the OIDC trust is pinned to, and the state bucket name, which contains the AWS account ID.

```bash
OWNER=$(gh api user --jq .login)
OWNER_ID=$(gh api user --jq .id)
REPO=self-healing-aws-infra
REPO_ID=$(gh api repos/$OWNER/$REPO --jq .id)
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

cat > bootstrap/terraform.tfvars <<EOF
github_owner    = "$OWNER"
github_owner_id = "$OWNER_ID"
github_repo_id  = "$REPO_ID"
EOF

sed -i "s/self-healing-aws-infra-tfstate-[0-9]*/self-healing-aws-infra-tfstate-$ACCOUNT/" envs/dev/providers.tf
```

`terraform.tfvars` is ignored by git. The trust policies match on GitHub's numeric owner and repository IDs, not only on names, so a repository that is deleted and recreated under the same name cannot assume the roles.

Check: `grep tfstate envs/dev/providers.tf` shows your account ID.

## 3. Bootstrap

The bootstrap creates what the pipeline itself needs before it can run: the versioned, encrypted state bucket, the GitHub OIDC identity provider, and three roles with their policies. It uses local state and your administrator credentials, and is applied once.

```bash
make bootstrap        # terraform init && terraform apply, answer yes
```

| Role | Assumed by | Can do |
|---|---|---|
| `self-healing-aws-infra-github-actions` | `main` and the `prod` environment | Build and destroy the environment |
| `self-healing-aws-infra-backend-deploy` | the `backend` branch | Upload releases and send the deploy command to tagged instances |
| `self-healing-aws-infra-frontend-deploy` | the `frontend` branch | Sync the SPA to its bucket and invalidate CloudFront |

Check: `terraform -chdir=bootstrap output` prints three role ARNs and the state bucket name.

## 4. Configure GitHub

```bash
gh variable set AWS_ROLE_ARN                 --body "$(terraform -chdir=bootstrap output -raw github_actions_role_arn)"
gh variable set AWS_BACKEND_DEPLOY_ROLE_ARN  --body "$(terraform -chdir=bootstrap output -raw backend_deploy_role_arn)"
gh variable set AWS_FRONTEND_DEPLOY_ROLE_ARN --body "$(terraform -chdir=bootstrap output -raw frontend_deploy_role_arn)"
gh variable set ALERT_EMAIL                  --body "you@example.com"
gh variable set BACKEND_DEPLOY_ENABLED       --body true
gh variable set FRONTEND_DEPLOY_ENABLED      --body true

echo "{\"reviewers\":[{\"type\":\"User\",\"id\":$OWNER_ID}]}" | \
  gh api --method PUT repos/$OWNER/$REPO/environments/prod --input -
```

The alert address lives only in a repository variable, so it is never written into a file. The `prod` environment holds `apply` and `destroy` until a reviewer approves them, and it is the only environment the Terraform role's trust policy accepts besides `main`.

Check: `gh variable list` shows six variables, and `gh api repos/$OWNER/$REPO/environments/prod --jq '.protection_rules'` lists a required reviewer.

## 5. Build the environment

Commit the edited state bucket name so the pipeline uses it, then start the workflow.

```bash
git add envs/dev/providers.tf
git commit -m "Point the state backend at my account"
git push
gh workflow run terraform.yml
gh run watch
```

The `plan` job runs on its own. When `apply` is waiting, approve it in the run's page under **Actions**. The first apply took about six and a half minutes; a Multi-AZ database adds several minutes. When it finishes, the `destroy` job appears and waits. Leave it waiting until you are done.

The workflow runs only on changes under `envs/` or `modules/`, or by manual dispatch. A change to `bootstrap/` or `lambdas/` does not start it; use `gh workflow run terraform.yml` after editing those.

Check:

```bash
aws lambda get-function --function-name self-healing-aws-infra-remediate --query 'Configuration.[State,LastUpdateStatus]'
aws events list-rules --name-prefix self-healing --query 'Rules[].[Name,State]'
aws configservice describe-config-rules --query 'ConfigRules[].[ConfigRuleName,ConfigRuleState]'
```

The function should be `Active` and `Successful`, the EventBridge rule `ENABLED`, and six Config rules `ACTIVE`.

## 6. Confirm the alert subscription

AWS sends a confirmation email to `ALERT_EMAIL`, from `no-reply@sns.amazonaws.com`, subject "AWS Notification - Subscription Confirmation". It often lands in spam. Click **Confirm subscription**. Do not click the unsubscribe link at the bottom, which deletes the subscription.

Check:

```bash
aws sns list-subscriptions-by-topic \
  --topic-arn "arn:aws:sns:us-east-1:$ACCOUNT:self-healing-aws-infra-alerts" \
  --query 'Subscriptions[].[Endpoint,SubscriptionArn]' --output text
```

The second column must be a real ARN, not `PendingConfirmation` or `Deleted`. If it is `Deleted`, subscribe again with `aws sns subscribe --topic-arn ... --protocol email --notification-endpoint you@example.com` and confirm the new message.

## 7. Deploy the application

The API and the SPA ship from their own branches. Push a commit to each so its pipeline runs with the variables you set.

```bash
for b in backend frontend; do
  git checkout $b && git commit --allow-empty -m "Deploy" && git push origin $b
done
git checkout main
gh run list --limit 4
```

The backend pipeline tests the API, uploads a release tarball, deploys it to the instances one at a time through Systems Manager (failing the run if any instance fails) and then promotes it to `latest`. The frontend pipeline builds the SPA, syncs it to its bucket and waits for a CloudFront invalidation.

Check:

```bash
DOMAIN=$(aws cloudfront list-distributions \
  --query "DistributionList.Items[?Comment=='self-healing-aws-infra'].DomainName | [0]" --output text)
curl -s https://$DOMAIN/api/health
```

The response is JSON with the database clock, a todo count and the release version. Open `https://$DOMAIN` to use the app. A request sent straight to the load balancer's DNS name is refused, because its security group accepts only CloudFront.

## 8. Break things on purpose

```bash
make chaos-s3     # remove Block Public Access from the site bucket
make chaos-sg     # open port 22 to the world on the app security group
make chaos-ec2    # downgrade an instance off IMDSv2
make chaos-ct     # stop the CloudTrail trail
```

Each script prints the time it broke the resource, then `outcome=remediated` and the seconds it took to become compliant, and appends the line to `chaos/results.log`. Run them with your own credentials: the remediation deliberately ignores changes made by the pipeline's role, so a script run as that role would not be healed.

```bash
aws logs tail /aws/lambda/self-healing-aws-infra-remediate --since 10m
```

Expect one JSON line per violation, with the rule, the API call, the action taken, `t0`, `t2` and a `correlation_id`, and an email with the same fields. `make chaos-rds` exists but is documented as a [known limit](mttr.md#known-limit-rds-1).

To collect a sample, run one script repeatedly with a pause so each run's follow-up events settle:

```bash
for i in $(seq 10); do sleep 15; make -s chaos-s3; done
cat chaos/results.log
```

## 9. Run the tests

```bash
cd lambdas
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest && black --check . && flake8
```

## 10. Tear it down

Start the workflow again and approve `apply` (nothing changes on a converged environment), then approve the `destroy` job when it appears.

```bash
gh workflow run terraform.yml
gh run watch
```

Check that nothing is left:

```bash
aws ec2 describe-instances --filters Name=tag:Project,Values=self-healing-aws-infra Name=instance-state-name,Values=pending,running,stopped --query 'Reservations[].Instances[].InstanceId'
aws rds describe-db-instances --query 'DBInstances[].DBInstanceIdentifier'
aws ec2 describe-nat-gateways --filter Name=state,Values=available,pending --query 'NatGateways[].NatGatewayId'
aws elbv2 describe-load-balancers --query 'LoadBalancers[].LoadBalancerName'
aws configservice describe-configuration-recorders --query 'ConfigurationRecorders[].name'
terraform -chdir=envs/dev init -input=false >/dev/null && terraform -chdir=envs/dev state list | wc -l
```

Every list should be empty and the state count `0`. The state bucket and the OIDC roles from the bootstrap remain, and they cost nothing while idle. To remove them too, empty the state bucket and run `terraform destroy` in `bootstrap/` (the bucket has `prevent_destroy` set, so remove that line first).

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `apply` fails with `AccessDenied` on a call the environment needs | The CI role's policies live in `bootstrap/`, which the pipeline cannot change. Add the missing service-level grant to the matching file in `bootstrap/`, run `make bootstrap`, and dispatch the workflow again |
| `apply` fails creating the Config service-linked role, saying it exists | Your account already has `AWSServiceRoleForConfig`. Import it: `cd envs/dev && terraform init && terraform import module.detection.aws_iam_service_linked_role.config arn:aws:iam::$ACCOUNT:role/aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig`, then dispatch again |
| Pushing a change did not start the workflow | Only `envs/**` and `modules/**` trigger it on push. Use `gh workflow run terraform.yml` |
| The subscription shows `Deleted` | The unsubscribe link was clicked. Subscribe again and confirm the new email |
| A chaos script says `not compliant before the run` | A previous run left the resource broken. Fix it by hand or wait for the remediation, then rerun |
| A chaos script reports success but nothing was logged | It was run as the pipeline's role, which the healer ignores, or the run raced the resource. Check `chaos/results.log` against the Lambda log |
| The backend or frontend pipeline skips its deploy job | `BACKEND_DEPLOY_ENABLED` or `FRONTEND_DEPLOY_ENABLED` is not `true`, or the run was a pull request |
