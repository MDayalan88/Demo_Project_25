resource "aws_lambda_function" "fileferry_agent" {
  function_name = "FileFerryAgent"
  handler       = "src.handlers.transfer_handler.lambda_handler"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_exec.arn
  timeout       = 30

  source_code_hash = filebase64sha256("path/to/your/deployment/package.zip")

  environment {
    DD_ENABLED          = var.dd_enabled
    DD_AGENT_HOST       = var.dd_agent_host
    DD_STATSD_PORT      = var.dd_statsd_port
    TEAMS_WEBHOOK_URL   = var.teams_webhook_url
    AWS_REGION          = var.aws_region
    AWS_ACCESS_KEY_ID   = var.aws_access_key_id
    AWS_SECRET_ACCESS_KEY = var.aws_secret_access_key
    FILEFERRY_CONFIG_PATH = var.fileferry_config_path
    FILEFERRY_NUM_WORKERS = var.fileferry_num_workers
    FILEFERRY_LOG_LEVEL   = var.fileferry_log_level
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_logs]
}

resource "aws_iam_role" "lambda_exec" {
  name = "fileferry_lambda_exec_role"

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

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_exec.name
}