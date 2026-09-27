locals {
  api_sources = ["aws.s3", "aws.ec2", "aws.rds", "aws.cloudtrail"]

  capture_patterns = {
    api-writes = {
      source      = local.api_sources
      detail-type = ["AWS API Call via CloudTrail"]
      detail      = { readOnly = [false] }
    }
    api-reads = {
      source      = local.api_sources
      detail-type = ["AWS API Call via CloudTrail"]
      detail      = { readOnly = [true] }
    }
    config = {
      source = ["aws.config"]
    }
  }
}

resource "aws_cloudwatch_log_group" "capture" {
  for_each = local.capture_patterns

  name              = "/aws/events/${var.project}-capture-${each.key}"
  retention_in_days = 3
}

data "aws_iam_policy_document" "capture" {
  statement {
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = [for group in aws_cloudwatch_log_group.capture : "${group.arn}:*"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com", "delivery.logs.amazonaws.com"]
    }
  }
}

resource "aws_cloudwatch_log_resource_policy" "capture" {
  policy_name     = "${var.project}-capture"
  policy_document = data.aws_iam_policy_document.capture.json
}

resource "aws_cloudwatch_event_rule" "capture" {
  for_each = local.capture_patterns

  name          = "${var.project}-capture-${each.key}"
  event_pattern = jsonencode(each.value)
}

resource "aws_cloudwatch_event_target" "capture" {
  for_each = local.capture_patterns

  rule = aws_cloudwatch_event_rule.capture[each.key].name
  arn  = aws_cloudwatch_log_group.capture[each.key].arn

  depends_on = [aws_cloudwatch_log_resource_policy.capture]
}
