resource "aws_lb" "main" {
  name                       = "${var.project}-alb"
  load_balancer_type         = "application"
  internal                   = false
  subnets                    = var.public_subnet_ids
  security_groups            = [var.alb_sg_id]
  drop_invalid_header_fields = true

  tags = {
    Name = "${var.project}-alb"
  }
}
