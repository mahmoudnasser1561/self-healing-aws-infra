output "remediate_function" {
  value = aws_lambda_function.remediate.function_name
}

output "remediate_function_arn" {
  value = aws_lambda_function.remediate.arn
}
