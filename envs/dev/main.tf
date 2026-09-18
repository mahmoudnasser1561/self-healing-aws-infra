data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "hello_world" {
  bucket = "${var.project_name}-hello-world-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "hello_world" {
  bucket = aws_s3_bucket.hello_world.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "hello_world" {
  bucket = aws_s3_bucket.hello_world.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "hello_world" {
  bucket = aws_s3_bucket.hello_world.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
