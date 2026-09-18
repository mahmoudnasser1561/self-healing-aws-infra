variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name, used for resource naming and tags"
  type        = string
  default     = "self-healing-aws-infra"
}

variable "github_owner" {
  description = "GitHub org or user that owns the repository"
  type        = string
  default     = "mahmoudnasser1561"
}

variable "github_owner_id" {
  description = "Numeric GitHub user/org ID (gh api user --jq .id)"
  type        = string
  default     = "106815734"
}

variable "github_repo" {
  description = "GitHub repository name, without owner"
  type        = string
  default     = "self-healing-aws-infra"
}

variable "github_repo_id" {
  description = "Numeric GitHub repository ID (gh api repos/<owner>/<repo> --jq .id)"
  type        = string
  default     = "1375786115"
}

variable "github_environment" {
  description = "GitHub Environment name the apply role's trust policy is scoped to"
  type        = string
  default     = "prod"
}
