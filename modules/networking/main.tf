data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_availability_zones" "available" {
  state = "available"

  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

locals {
  azs         = slice(data.aws_availability_zones.available.names, 0, 2)
  az_suffixes = [for az in local.azs : substr(az, -1, 1)]

  vpc_cidr     = "10.0.0.0/16"
  public_cidrs = ["10.0.0.0/24", "10.0.1.0/24"]
  app_cidrs    = ["10.0.10.0/24", "10.0.11.0/24"]
  data_cidrs   = ["10.0.20.0/24", "10.0.21.0/24"]
}

resource "aws_vpc" "main" {
  cidr_block           = local.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.project}-vpc"
  }
}
