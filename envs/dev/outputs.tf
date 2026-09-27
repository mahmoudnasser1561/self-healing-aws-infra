output "alb_dns_name" {
  value = module.backend.alb_dns_name
}

output "asg_name" {
  value = module.backend.asg_name
}

output "releases_bucket" {
  value = module.backend.releases_bucket
}

output "cloudfront_domain" {
  value = module.frontend.cloudfront_domain
}

output "distribution_id" {
  value = module.frontend.distribution_id
}

output "frontend_bucket" {
  value = module.frontend.frontend_bucket
}

output "waf_log_group" {
  value = module.frontend.waf_log_group
}

output "alb_logs_bucket" {
  value = module.backend.alb_logs_bucket
}

output "cloudfront_logs_bucket" {
  value = module.frontend.cloudfront_logs_bucket
}

output "capture_log_groups" {
  value = module.detection.capture_log_groups
}

output "config_rule_names" {
  value = module.detection.config_rule_names
}
