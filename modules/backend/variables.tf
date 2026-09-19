variable "project" {
  type = string
}

variable "db_secret_arn" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "alb_sg_id" {
  type = string
}
