# FileFerry Agent - README

## Overview
FileFerry Agent is a file transfer application designed to facilitate the movement of files between various storage systems, including SFTP, FTP, and AWS S3. The application is built using Python and leverages AWS services for deployment and scalability.

## Project Structure
```
fileferry-agent
├── src
│   ├── handlers
│   ├── services
│   ├── utils
│   └── models
├── infrastructure
│   ├── terraform
│   └── cloudformation
├── tests
│   ├── unit
│   └── integration
├── config
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── docker-compose.yml
├── buildspec.yml
├── .gitignore
└── README.md
```

## Features
- **Multi-Protocol Support**: Transfer files using SFTP, FTP, and AWS S3.
- **Notification Service**: Get notified about transfer statuses through various channels.
- **Monitoring Service**: Track performance and status of file transfers.
- **Configurable**: Load settings from JSON files and environment variables.

## Getting Started

### Prerequisites
- Python 3.x
- AWS Account
- Docker (for containerization)

### Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd fileferry-agent
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Copy `.env.example` to `.env` and fill in your credentials.

### Running the Application
- To run the application locally, use Docker:
  ```
  docker-compose up
  ```

### Deployment
- Use Terraform to provision AWS resources:
  ```
  cd infrastructure/terraform
  terraform init
  terraform apply
  ```

### Testing
- Run unit tests:
  ```
  pytest tests/unit
  ```

- Run integration tests:
  ```
  pytest tests/integration
  ```

## Cost Comparison: AWS vs Azure
- **AWS**:
  - S3 storage pricing based on data stored and requests made.
  - Lambda pricing based on requests and execution duration.
  
- **Azure**:
  - Blob Storage pricing similar to S3.
  - Functions pricing based on execution time and number of executions.

## Summary
FileFerry Agent provides a robust solution for file transfers across multiple protocols, with a focus on AWS for deployment. The choice between AWS and Azure will depend on specific use cases and pricing considerations.