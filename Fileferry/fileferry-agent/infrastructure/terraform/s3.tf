resource "aws_s3_bucket" "fileferry_bucket" {
  bucket = "fileferry-agent-bucket"
  acl    = "private"

  tags = {
    Name        = "FileFerry Agent Bucket"
    Environment = "Development"
  }
}

resource "aws_s3_bucket_versioning" "fileferry_bucket_versioning" {
  bucket = aws_s3_bucket.fileferry_bucket.id

  versioning_configuration {
    enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "fileferry_bucket_lifecycle" {
  bucket = aws_s3_bucket.fileferry_bucket.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      days = 30
    }
  }
}

output "s3_bucket_name" {
  value = aws_s3_bucket.fileferry_bucket.bucket
}