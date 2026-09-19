data "aws_iam_policy_document" "backend_deploy_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${local.github_qualified_repo}:ref:refs/heads/${var.github_backend_branch}"]
    }
  }
}

resource "aws_iam_role" "backend_deploy" {
  name               = "${var.project}-backend-deploy"
  assume_role_policy = data.aws_iam_policy_document.backend_deploy_trust.json
}

data "aws_iam_policy_document" "backend_deploy" {
  statement {
    sid    = "ReleasesBucket"
    effect = "Allow"
    actions = [
      "s3:AbortMultipartUpload",
      "s3:GetBucketLocation",
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
      "s3:ListBucketVersions",
      "s3:PutObject",
    ]
    resources = [
      "arn:aws:s3:::${var.project}-app-releases-${local.account_id}",
      "arn:aws:s3:::${var.project}-app-releases-${local.account_id}/*",
    ]
  }

  statement {
    sid       = "DeployCommandDocument"
    effect    = "Allow"
    actions   = ["ssm:SendCommand"]
    resources = ["arn:aws:ssm:${var.aws_region}::document/AWS-RunShellScript"]
  }

  statement {
    sid       = "DeployCommandTargets"
    effect    = "Allow"
    actions   = ["ssm:SendCommand"]
    resources = ["arn:aws:ec2:${var.aws_region}:${local.account_id}:instance/*"]

    condition {
      test     = "StringEquals"
      variable = "ssm:resourceTag/Project"
      values   = [var.project]
    }
  }

  statement {
    sid    = "DeployCommandStatus"
    effect = "Allow"
    actions = [
      "ssm:DescribeInstanceInformation",
      "ssm:DescribeInstanceProperties",
      "ssm:GetCommandInvocation",
      "ssm:ListCommandInvocations",
      "ssm:ListCommands",
    ]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [var.aws_region]
    }
  }

  statement {
    sid    = "RolloutChecks"
    effect = "Allow"
    actions = [
      "autoscaling:Describe*",
      "ec2:DescribeInstances",
      "elasticloadbalancing:Describe*",
    ]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [var.aws_region]
    }
  }
}

resource "aws_iam_role_policy" "backend_deploy" {
  name   = "${var.project}-backend-deploy"
  role   = aws_iam_role.backend_deploy.id
  policy = data.aws_iam_policy_document.backend_deploy.json
}
