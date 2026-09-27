data "aws_iam_policy_document" "github_actions_selfheal" {
  statement {
    sid       = "RemediationFunctions"
    effect    = "Allow"
    actions   = ["lambda:*"]
    resources = ["arn:aws:lambda:${var.aws_region}:${local.account_id}:function:${var.project}-*"]
  }

  statement {
    sid       = "EventRules"
    effect    = "Allow"
    actions   = ["events:*"]
    resources = ["arn:aws:events:${var.aws_region}:${local.account_id}:rule/${var.project}-*"]
  }

  statement {
    sid       = "AlertTopics"
    effect    = "Allow"
    actions   = ["sns:*"]
    resources = ["arn:aws:sns:${var.aws_region}:${local.account_id}:${var.project}-*"]
  }

  statement {
    sid       = "DeadLetterQueues"
    effect    = "Allow"
    actions   = ["sqs:*"]
    resources = ["arn:aws:sqs:${var.aws_region}:${local.account_id}:${var.project}-*"]
  }

  statement {
    sid       = "Alarms"
    effect    = "Allow"
    actions   = ["cloudwatch:*"]
    resources = ["arn:aws:cloudwatch:${var.aws_region}:${local.account_id}:alarm:${var.project}-*"]
  }

  statement {
    sid       = "AlarmsDescribe"
    effect    = "Allow"
    actions   = ["cloudwatch:DescribeAlarms", "cloudwatch:ListTagsForResource"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [var.aws_region]
    }
  }

  statement {
    sid       = "Trails"
    effect    = "Allow"
    actions   = ["cloudtrail:*"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [var.aws_region]
    }
  }

  statement {
    sid     = "FunctionLogGroups"
    effect  = "Allow"
    actions = ["logs:*"]
    resources = [
      "arn:aws:logs:${var.aws_region}:${local.account_id}:log-group:/aws/lambda/${var.project}-*",
      "arn:aws:logs:${var.aws_region}:${local.account_id}:log-group:/aws/lambda/${var.project}-*:*",
    ]
  }

  statement {
    sid       = "ConfigService"
    effect    = "Allow"
    actions   = ["config:*"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [var.aws_region]
    }
  }

  statement {
    sid    = "ConfigServiceLinkedRole"
    effect = "Allow"
    actions = [
      "iam:CreateServiceLinkedRole",
      "iam:DeleteServiceLinkedRole",
      "iam:GetRole",
      "iam:GetServiceLinkedRoleDeletionStatus",
      "iam:ListRoleTags",
    ]
    resources = ["arn:aws:iam::${local.account_id}:role/aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig"]
  }

  statement {
    sid       = "ConfigPassRole"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = ["arn:aws:iam::${local.account_id}:role/aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig"]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["config.amazonaws.com"]
    }
  }

  statement {
    sid     = "EventCaptureLogGroups"
    effect  = "Allow"
    actions = ["logs:*"]
    resources = [
      "arn:aws:logs:${var.aws_region}:${local.account_id}:log-group:/aws/events/${var.project}-*",
      "arn:aws:logs:${var.aws_region}:${local.account_id}:log-group:/aws/events/${var.project}-*:*",
    ]
  }

  statement {
    sid     = "ConfigBucket"
    effect  = "Allow"
    actions = ["s3:*"]
    resources = [
      "arn:aws:s3:::${var.project}-config-*",
      "arn:aws:s3:::${var.project}-config-*/*",
    ]
  }

  statement {
    sid     = "TrailBucket"
    effect  = "Allow"
    actions = ["s3:*"]
    resources = [
      "arn:aws:s3:::${var.project}-trail-*",
      "arn:aws:s3:::${var.project}-trail-*/*",
    ]
  }
}

resource "aws_iam_policy" "github_actions_selfheal" {
  name   = "${var.project}-selfheal"
  policy = data.aws_iam_policy_document.github_actions_selfheal.json
}

resource "aws_iam_role_policy_attachment" "github_actions_selfheal" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions_selfheal.arn
}
