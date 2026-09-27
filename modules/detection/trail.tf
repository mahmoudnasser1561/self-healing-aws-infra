locals {
  trail_arn = "arn:aws:cloudtrail:${local.region}:${local.account_id}:trail/${var.project}"
}

resource "aws_s3_bucket" "trail" {
  count = var.create_trail ? 1 : 0

  bucket        = "${var.project}-trail-${local.account_id}"
  force_destroy = true

  tags = {
    Name = "${var.project}-trail"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "trail" {
  count = var.create_trail ? 1 : 0

  bucket = aws_s3_bucket.trail[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "trail" {
  count = var.create_trail ? 1 : 0

  bucket = aws_s3_bucket.trail[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "trail" {
  count = var.create_trail ? 1 : 0

  bucket = aws_s3_bucket.trail[0].id

  rule {
    id     = "expire"
    status = "Enabled"

    filter {}

    expiration {
      days = 7
    }
  }
}

data "aws_iam_policy_document" "trail" {
  count = var.create_trail ? 1 : 0

  statement {
    sid       = "AclCheck"
    actions   = ["s3:GetBucketAcl"]
    resources = [aws_s3_bucket.trail[0].arn]

    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = [local.trail_arn]
    }
  }

  statement {
    sid       = "Write"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.trail[0].arn}/AWSLogs/${local.account_id}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = [local.trail_arn]
    }
  }
}

resource "aws_s3_bucket_policy" "trail" {
  count = var.create_trail ? 1 : 0

  bucket = aws_s3_bucket.trail[0].id
  policy = data.aws_iam_policy_document.trail[0].json

  depends_on = [aws_s3_bucket_public_access_block.trail]
}

resource "aws_cloudtrail" "main" {
  count = var.create_trail ? 1 : 0

  name                       = var.project
  s3_bucket_name             = aws_s3_bucket.trail[0].id
  enable_log_file_validation = true

  depends_on = [aws_s3_bucket_policy.trail]
}
