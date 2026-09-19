output "releases_bucket" {
  value = aws_s3_bucket.releases.id
}

output "alb_dns_name" {
  value = aws_lb.main.dns_name
}
