output "alb_dns_name" {
  value = module.backend.alb_dns_name
}

output "asg_name" {
  value = module.backend.asg_name
}

output "releases_bucket" {
  value = module.backend.releases_bucket
}
