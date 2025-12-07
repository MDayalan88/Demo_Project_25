resource "aws_secretsmanager_secret" "fileferry_secret" {
  name        = "FileFerrySecret"
  description = "Secret for FileFerry Agent credentials"
}

resource "aws_secretsmanager_secret_version" "fileferry_secret_version" {
  secret_id     = aws_secretsmanager_secret.fileferry_secret.id
  secret_string = jsonencode({
    AWS_ACCESS_KEY_ID     = var.aws_access_key_id
    AWS_SECRET_ACCESS_KEY = var.aws_secret_access_key
    TEAMS_WEBHOOK_URL     = var.teams_webhook_url
  })
}