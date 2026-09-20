data "aws_iam_policy_document" "github_actions_frontend" {
  statement {
    sid       = "CloudFront"
    effect    = "Allow"
    actions   = ["cloudfront:*"]
    resources = ["*"]
  }

  statement {
    sid       = "WebAcl"
    effect    = "Allow"
    actions   = ["wafv2:*"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [var.aws_region]
    }
  }

  statement {
    sid     = "WebAclLogGroups"
    effect  = "Allow"
    actions = ["logs:*"]
    resources = [
      "arn:aws:logs:${var.aws_region}:${local.account_id}:log-group:aws-waf-logs-${var.project}*",
      "arn:aws:logs:${var.aws_region}:${local.account_id}:log-group:aws-waf-logs-${var.project}*:*",
    ]
  }

  statement {
    sid    = "LogDelivery"
    effect = "Allow"
    actions = [
      "logs:CreateLogDelivery",
      "logs:DeleteLogDelivery",
      "logs:DeleteResourcePolicy",
      "logs:DescribeResourcePolicies",
      "logs:GetLogDelivery",
      "logs:ListLogDeliveries",
      "logs:PutResourcePolicy",
      "logs:UpdateLogDelivery",
    ]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [var.aws_region]
    }
  }

  statement {
    sid     = "FrontendBucket"
    effect  = "Allow"
    actions = ["s3:*"]
    resources = [
      "arn:aws:s3:::${var.project}-frontend-*",
      "arn:aws:s3:::${var.project}-frontend-*/*",
    ]
  }

  statement {
    sid       = "CloudFrontPrefixList"
    effect    = "Allow"
    actions   = ["ec2:GetManagedPrefixListEntries"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [var.aws_region]
    }
  }
}

resource "aws_iam_policy" "github_actions_frontend" {
  name   = "${var.project}-frontend"
  policy = data.aws_iam_policy_document.github_actions_frontend.json
}

resource "aws_iam_role_policy_attachment" "github_actions_frontend" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions_frontend.arn
}
