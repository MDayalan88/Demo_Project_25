resource "aws_s3_bucket" "fileferry_bucket" {
  bucket = "fileferry-agent-bucket"
  acl    = "private"

  tags = {
    Name        = "FileFerry Agent Bucket"
    Environment = "Production"
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "fileferry_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Effect = "Allow"
        Sid    = ""
      },
    ]
  })
}

resource "aws_iam_policy" "lambda_policy" {
  name        = "fileferry_lambda_policy"
  description = "Policy for FileFerry Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = [
          aws_s3_bucket.fileferry_bucket.arn,
          "${aws_s3_bucket.fileferry_bucket.arn}/*"
        ]
      },
      {
        Action = "logs:*"
        Effect = "Allow"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  policy_arn = aws_iam_policy.lambda_policy.arn
  role       = aws_iam_role.lambda_role.name
}

resource "aws_lambda_function" "fileferry_lambda" {
  function_name = "fileferry_lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "app.handler"
  runtime       = "python3.8"

  source_code_hash = filebase64sha256("path/to/your/deployment/package.zip")

  environment = {
    S3_BUCKET = aws_s3_bucket.fileferry_bucket.bucket
  }
}

resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name = "/aws/lambda/${aws_lambda_function.fileferry_lambda.function_name}"
}

resource "aws_eventbridge_rule" "fileferry_event_rule" {
  name        = "fileferry_event_rule"
  description = "Event rule for FileFerry Agent"

  event_pattern = jsonencode({
    source = ["aws.s3"]
    detail_type = ["AWS API Call via CloudTrail"]
    detail = {
      eventSource = ["s3.amazonaws.com"]
      eventName   = ["PutObject"]
    }
  })
}

resource "aws_eventbridge_target" "fileferry_lambda_target" {
  rule      = aws_eventbridge_rule.fileferry_event_rule.name
  target_id = "fileferry_lambda"
  arn       = aws_lambda_function.fileferry_lambda.arn
}