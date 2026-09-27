output "config_rule_names" {
  value = [for rule in aws_config_config_rule.managed : rule.name]
}

output "config_bucket" {
  value = aws_s3_bucket.config.id
}

output "api_writes_rule" {
  value = {
    name = aws_cloudwatch_event_rule.api_writes.name
    arn  = aws_cloudwatch_event_rule.api_writes.arn
  }
}
