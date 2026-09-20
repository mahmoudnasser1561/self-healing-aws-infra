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
