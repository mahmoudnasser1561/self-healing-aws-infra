output "github_actions_role_arn" {
  description = "IAM role ARN GitHub Actions assumes via OIDC. Set this as the repo variable AWS_ROLE_ARN."
  value       = aws_iam_role.github_actions.arn
}

output "tf_state_bucket" {
  description = "S3 bucket name for Terraform remote state (envs/dev/providers.tf backend)"
  value       = aws_s3_bucket.terraform_state.id
}

output "aws_region" {
  description = "AWS region all resources are created in"
  value       = var.aws_region
}

output "backend_deploy_role_arn" {
  description = "IAM role ARN the backend branch pipeline assumes via OIDC. Set this as the repo variable AWS_BACKEND_DEPLOY_ROLE_ARN."
  value       = aws_iam_role.backend_deploy.arn
}
