variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "self-healing-aws-infra"
}

variable "create_trail" {
  type    = bool
  default = true
}

variable "alert_email" {
  type    = string
  default = ""
}
