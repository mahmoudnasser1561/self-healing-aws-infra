data "archive_file" "remediate" {
  type        = "zip"
  source_dir  = "${path.module}/../../lambdas/remediate"
  output_path = "${path.module}/remediate.zip"
}

data "aws_iam_policy_document" "remediate_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "remediate" {
  name               = "${var.project}-remediate"
  assume_role_policy = data.aws_iam_policy_document.remediate_assume.json
}

data "aws_iam_policy_document" "remediate" {
  statement {
    sid       = "S3PublicAccessBlock"
    actions   = ["s3:GetBucketPublicAccessBlock", "s3:PutBucketPublicAccessBlock"]
    resources = ["arn:aws:s3:::${var.project}-*"]
  }

  statement {
    sid       = "SecurityGroupRead"
    actions   = ["ec2:DescribeSecurityGroups", "ec2:DescribeSecurityGroupRules"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [local.region]
    }
  }

  statement {
    sid       = "SecurityGroupRevoke"
    actions   = ["ec2:RevokeSecurityGroupIngress"]
    resources = ["arn:aws:ec2:${local.region}:${local.account_id}:security-group/*"]
  }

  statement {
    sid       = "InstanceMetadata"
    actions   = ["ec2:DescribeInstances", "ec2:ModifyInstanceMetadataOptions"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [local.region]
    }
  }

  statement {
    sid       = "RdsPublicAccess"
    actions   = ["rds:DescribeDBInstances", "rds:ModifyDBInstance"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [local.region]
    }
  }

  statement {
    sid       = "TrailLogging"
    actions   = ["cloudtrail:GetTrailStatus", "cloudtrail:StartLogging"]
    resources = ["arn:aws:cloudtrail:${local.region}:${local.account_id}:trail/${var.project}*"]
  }

  statement {
    sid       = "Notify"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.alerts.arn]
  }

  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.remediate.arn}:*"]
  }
}

resource "aws_iam_role_policy" "remediate" {
  name   = "${var.project}-remediate"
  role   = aws_iam_role.remediate.id
  policy = data.aws_iam_policy_document.remediate.json
}

resource "aws_cloudwatch_log_group" "remediate" {
  name              = "/aws/lambda/${var.project}-remediate"
  retention_in_days = 7
}

resource "aws_lambda_function" "remediate" {
  function_name    = "${var.project}-remediate"
  role             = aws_iam_role.remediate.arn
  runtime          = "python3.12"
  handler          = "handler.handler"
  filename         = data.archive_file.remediate.output_path
  source_code_hash = data.archive_file.remediate.output_base64sha256
  timeout          = 30
  memory_size      = 128

  environment {
    variables = {
      PROJECT_PREFIX = "${var.project}-"
      TOPIC_ARN      = aws_sns_topic.alerts.arn
      EXEMPT_ROLE_ARNS = join(",", [
        aws_iam_role.remediate.arn,
        "arn:aws:iam::${local.account_id}:role/${var.project}-github-actions",
      ])
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.remediate,
    aws_iam_role_policy.remediate,
  ]
}
