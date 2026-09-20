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

module "backend" {
  source = "../../modules/backend"

  project           = var.project_name
  vpc_id            = module.networking.vpc_id
  public_subnet_ids = module.networking.public_subnet_ids
  alb_sg_id         = module.security.alb_sg_id
  app_sg_id         = module.security.app_sg_id
  db_address        = module.data.db_address
  db_secret_arn     = module.data.db_secret_arn
}
