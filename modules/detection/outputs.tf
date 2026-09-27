output "capture_log_groups" {
  value = { for name, group in aws_cloudwatch_log_group.capture : name => group.name }
}

output "config_rule_names" {
  value = [for rule in aws_config_config_rule.managed : rule.name]
}

output "config_bucket" {
  value = aws_s3_bucket.config.id
}
