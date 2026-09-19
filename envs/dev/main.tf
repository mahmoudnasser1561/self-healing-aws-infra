module "networking" {
  source = "../../modules/networking"

  project = var.project_name
}

module "security" {
  source = "../../modules/security"

  project = var.project_name
  vpc_id  = module.networking.vpc_id
}

module "data" {
  source = "../../modules/data"

  project         = var.project_name
  data_subnet_ids = module.networking.data_subnet_ids
  data_sg_id      = module.security.data_sg_id
}
