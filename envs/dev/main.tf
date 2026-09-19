module "networking" {
  source = "../../modules/networking"

  project = var.project_name
}

module "security" {
  source = "../../modules/security"

  project = var.project_name
  vpc_id  = module.networking.vpc_id
}
