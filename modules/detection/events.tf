locals {
  api_sources = ["aws.s3", "aws.ec2", "aws.rds", "aws.cloudtrail"]
}

resource "aws_cloudwatch_event_rule" "api_writes" {
  name = "${var.project}-api-writes"

  event_pattern = jsonencode({
    source      = local.api_sources
    detail-type = ["AWS API Call via CloudTrail"]
    detail      = { readOnly = [false] }
  })
}

