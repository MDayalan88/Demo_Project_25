variable "aws_region" {
  description = "The AWS region where resources will be deployed"
  type        = string
  default     = "us-east-1"
}

variable "s3_bucket_name" {
  description = "The name of the S3 bucket for file storage"
  type        = string
}

variable "lambda_function_name" {
  description = "The name of the AWS Lambda function"
  type        = string
}

variable "lambda_role_arn" {
  description = "The ARN of the IAM role for the Lambda function"
  type        = string
}

variable "eventbridge_rule_name" {
  description = "The name of the EventBridge rule"
  type        = string
}

variable "secrets_manager_secret_name" {
  description = "The name of the secret in AWS Secrets Manager"
  type        = string
}