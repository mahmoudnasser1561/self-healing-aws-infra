data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github.certificates[0].sha1_fingerprint]
}

locals {
  github_qualified_repo = "${var.github_owner}@${var.github_owner_id}/${var.github_repo}@${var.github_repo_id}"
}

data "aws_iam_policy_document" "plan_assume_role" {
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
      values   = ["repo:${local.github_qualified_repo}:pull_request"]
    }
  }
}

resource "aws_iam_role" "plan" {
  name               = "${var.project_name}-plan"
  assume_role_policy = data.aws_iam_policy_document.plan_assume_role.json
}

data "aws_iam_policy_document" "plan_state_lock" {
  statement {
    sid    = "StateLockfile"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = ["${aws_s3_bucket.terraform_state.arn}/*.tflock"]
  }
}

resource "aws_iam_role_policy" "plan_state_lock" {
  name   = "state-lockfile"
  role   = aws_iam_role.plan.id
  policy = data.aws_iam_policy_document.plan_state_lock.json
}

resource "aws_iam_role_policy_attachment" "plan_readonly" {
  role       = aws_iam_role.plan.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

data "aws_iam_policy_document" "apply_assume_role" {
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
      values   = ["repo:${local.github_qualified_repo}:environment:${var.github_environment}"]
    }
  }
}

resource "aws_iam_role" "apply" {
  name               = "${var.project_name}-apply"
  assume_role_policy = data.aws_iam_policy_document.apply_assume_role.json
}

data "aws_iam_policy_document" "apply_stage0_permissions" {
  statement {
    sid    = "TerraformStateBucket"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.terraform_state.arn,
      "${aws_s3_bucket.terraform_state.arn}/*",
    ]
  }

  statement {
    sid    = "HelloWorldBucketLifecycle"
    effect = "Allow"
    actions = [
      "s3:CreateBucket",
      "s3:DeleteBucket",
      "s3:PutBucketVersioning",
      "s3:PutBucketPublicAccessBlock",
      "s3:PutBucketTagging",
      "s3:PutEncryptionConfiguration",
      "s3:GetBucketVersioning",
      "s3:GetBucketPolicy",
      "s3:GetEncryptionConfiguration",
      "s3:GetBucketPublicAccessBlock",
      "s3:GetBucketTagging",
      "s3:ListBucket",
    ]
    resources = ["arn:aws:s3:::${var.project_name}-hello-world-*"]
  }
}

resource "aws_iam_role_policy" "apply_stage0" {
  name   = "stage0-state-and-hello-world"
  role   = aws_iam_role.apply.id
  policy = data.aws_iam_policy_document.apply_stage0_permissions.json
}
