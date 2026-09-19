resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-data"
  subnet_ids = var.data_subnet_ids

  tags = {
    Name = "${var.project}-data"
  }
}

resource "aws_db_instance" "main" {
  identifier = "${var.project}-postgres"

  engine         = "postgres"
  engine_version = "16"
  instance_class = "db.t4g.micro"

  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name                     = "app"
  username                    = "dbadmin"
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.data_sg_id]
  publicly_accessible    = false
  multi_az               = false

  backup_retention_period = 0
  skip_final_snapshot     = true
  deletion_protection     = false

  tags = {
    Name = "${var.project}-postgres"
  }
}
