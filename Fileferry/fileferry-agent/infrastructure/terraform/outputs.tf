output.tf

output "s3_bucket_name" {
  value = aws_s3_bucket.fileferry_bucket.id
}

output "lambda_function_name" {
  value = aws_lambda_function.fileferry_lambda.function_name
}

output "iam_role_arn" {
  value = aws_iam_role.fileferry_role.arn
}

output "eventbridge_rule_arn" {
  value = aws_cloudwatch_event_rule.fileferry_event_rule.arn
}

output "secrets_manager_arn" {
  value = aws_secretsmanager_secret.fileferry_secret.arn
}