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
