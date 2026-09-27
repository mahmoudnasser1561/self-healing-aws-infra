resource "aws_cloudwatch_event_target" "trigger" {
  for_each = var.trigger_rules

  rule = each.value.name
  arn  = aws_lambda_function.remediate.arn
}

resource "aws_lambda_permission" "trigger" {
  for_each = var.trigger_rules

  statement_id  = "Allow${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.remediate.function_name
  principal     = "events.amazonaws.com"
  source_arn    = each.value.arn
}
