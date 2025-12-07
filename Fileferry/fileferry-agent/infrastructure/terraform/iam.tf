resource "aws_iam_role" "fileferry_role" {
  name               = "fileferry_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Effect    = "Allow"
        Sid       = ""
      },
    ]
  })
}

resource "aws_iam_policy" "fileferry_policy" {
  name        = "fileferry_policy"
  description = "Policy for FileFerry Agent to access S3 and other resources"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::your-s3-bucket-name",
          "arn:aws:s3:::your-s3-bucket-name/*"
        ]
      },
      {
        Effect = "Allow"
        Action = "logs:*"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = "secretsmanager:GetSecretValue"
        Resource = "arn:aws:secretsmanager:your-region:your-account-id:secret:your-secret-name"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "fileferry_attachment" {
  policy_arn = aws_iam_policy.fileferry_policy.arn
  role       = aws_iam_role.fileferry_role.name
}