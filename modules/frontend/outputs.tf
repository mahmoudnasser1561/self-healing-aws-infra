output "frontend_bucket" {
  value = aws_s3_bucket.site.id
}

output "cloudfront_domain" {
  value = aws_cloudfront_distribution.main.domain_name
}

output "distribution_id" {
  value = aws_cloudfront_distribution.main.id
}

output "waf_log_group" {
  value = aws_cloudwatch_log_group.waf.name
}
