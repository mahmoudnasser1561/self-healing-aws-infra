output "app_sg_id" {
  value = aws_security_group.app.id
}

output "data_sg_id" {
  value = aws_security_group.data.id
}
