data "aws_iam_policy_document" "frontend_deploy_trust" {
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
      values   = ["repo:${local.github_qualified_repo}:ref:refs/heads/${var.github_frontend_branch}"]
    }
  }
}

resource "aws_iam_role" "frontend_deploy" {
  name               = "${var.project}-frontend-deploy"
  assume_role_policy = data.aws_iam_policy_document.frontend_deploy_trust.json
}

data "aws_iam_policy_document" "frontend_deploy" {
  statement {
    sid    = "FrontendBucket"
    effect = "Allow"
    actions = [
      "s3:AbortMultipartUpload",
      "s3:DeleteObject",
      "s3:GetBucketLocation",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
      "s3:PutObject",
    ]
    resources = [
      "arn:aws:s3:::${var.project}-frontend-${local.account_id}",
      "arn:aws:s3:::${var.project}-frontend-${local.account_id}/*",
    ]
  }

  statement {
    sid    = "Invalidate"
    effect = "Allow"
    actions = [
      "cloudfront:CreateInvalidation",
      "cloudfront:GetInvalidation",
      "cloudfront:ListInvalidations",
    ]
    resources = ["arn:aws:cloudfront::${local.account_id}:distribution/*"]
  }

  statement {
    sid    = "FindTheDistribution"
    effect = "Allow"
    actions = [
      "cloudfront:GetDistribution",
      "cloudfront:ListDistributions",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "frontend_deploy" {
  name   = "${var.project}-frontend-deploy"
  role   = aws_iam_role.frontend_deploy.id
  policy = data.aws_iam_policy_document.frontend_deploy.json
}
