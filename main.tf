terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "us-east-1"
}

# Create a EC2 Instances
resource "aws_instance" "Demo-project" {
  ami = "ami-08a6efd148b1f7504"
  instance_type = "t3.micro"
}