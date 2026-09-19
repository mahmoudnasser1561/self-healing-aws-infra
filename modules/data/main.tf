resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-data"
  subnet_ids = var.data_subnet_ids

  tags = {
    Name = "${var.project}-data"
  }
}
