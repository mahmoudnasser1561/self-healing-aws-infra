variable "aws_region" {
  description = "AWS region for all project resources"
  type        = string
  default     = "us-east-1"
}

variable "github_owner" {
  description = "GitHub org or user that owns the repository"
  type        = string
  default     = "mahmoudnasser1561"
}

variable "github_repo" {
  description = "GitHub repository name (owner/repo, without owner)"
  type        = string
  default     = "self-healing-aws-infra"
}

variable "github_owner_id" {
  description = "Numeric GitHub user/org ID (gh api user --jq .id)"
  type        = string
  default     = "106815734"
}

variable "github_repo_id" {
  description = "Numeric GitHub repository ID (gh api repos/<owner>/<repo> --jq .id)"
  type        = string
  default     = "1375786115"
}

variable "project" {
  description = "Project tag value applied to every resource"
  type        = string
  default     = "self-healing-aws-infra"
}

variable "github_environment" {
  description = "GitHub Environment name the gated apply job runs under"
  type        = string
  default     = "prod"
}

variable "github_backend_branch" {
  type    = string
  default = "backend"
}

variable "github_frontend_branch" {
  type    = string
  default = "frontend"
}
