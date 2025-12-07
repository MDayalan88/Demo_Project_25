resource "aws_cloudwatch_event_rule" "fileferry_event_rule" {
  name        = "fileferry-event-rule"
  description = "Event rule for FileFerry Agent"
  event_pattern = jsonencode({
    "source" = ["com.fileferry"]
    "detail-type" = ["FileTransferStatus"]
  })
}

resource "aws_cloudwatch_event_target" "fileferry_lambda_target" {
  rule      = aws_cloudwatch_event_rule.fileferry_event_rule.name
  target_id = "FileFerryLambda"
  arn       = aws_lambda_function.fileferry_lambda.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fileferry_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.fileferry_event_rule.arn
}