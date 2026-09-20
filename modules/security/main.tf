resource "aws_security_group" "app" {
  name        = "${var.project}-app"
  description = "Application tier instances"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.project}-app"
  }
}

resource "aws_security_group" "data" {
  name        = "${var.project}-data"
  description = "Database tier"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.project}-data"
  }
}

resource "aws_security_group" "alb" {
  name        = "${var.project}-alb"
  description = "Load balancer"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.project}-alb"
  }
}

data "aws_ec2_managed_prefix_list" "cloudfront" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}
