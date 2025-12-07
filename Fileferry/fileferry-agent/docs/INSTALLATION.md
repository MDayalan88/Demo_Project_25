# FileFerry Agent - Installation & Setup Guide

## Overview

FileFerry Agent automates S3-to-FTP/SFTP file transfers with ServiceNow integration, SSO authentication, Teams notifications, and Datadog monitoring.

---

## Prerequisites

- Python 3.9 or higher
- AWS Account with S3 access
- ServiceNow instance with API access
- Microsoft Teams webhook (for notifications)
- Datadog account (for monitoring)
- FTP/SFTP server credentials

---

## Installation Steps

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Microsoft Agent Framework (REQUIRED --pre flag)
pip install agent-framework-azure-ai --pre
```

**Required packages** (added to requirements.txt):
```
fastapi
uvicorn
pydantic
aiohttp
boto3
botocore
datadog
pysftp
paramiko
asyncio
```

### 2. Configure AWS SSO

Set up AWS SSO authentication:

```bash
# Configure AWS CLI with SSO
aws configure sso

# Test SSO authentication
aws sso login --profile your-profile
```

Create IAM role for read-only S3 access:
- Role name: `FileFerryReadOnlyRole`
- Permissions: `s3:GetObject`, `s3:ListBucket`
- Trust policy: Allow STS AssumeRole

### 3. Configure ServiceNow

1. Create API user in ServiceNow
2. Grant permissions:
   - `incident.read`
   - `incident.write`
   - `incident.create`
3. Note instance URL and credentials

### 4. Set Up Microsoft Teams Webhook

1. In Teams, go to your channel
2. Click "..." → Connectors → Incoming Webhook
3. Name: "FileFerry Agent"
4. Copy webhook URL

### 5. Configure Datadog

1. Get API key from Datadog dashboard
2. Get Application key
3. Install Datadog agent (optional):
   ```bash
   DD_API_KEY=<your-key> bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script.sh)"
   ```

### 6. Update Configuration

Edit `config/fileferry_config.json`:

```json
{
  "fileFerry": {
    "aws": {
      "sso": {
        "sso_start_url": "https://your-sso-portal.awsapps.com/start",
        "sso_region": "us-east-1",
        "account_id": "123456789012",
        "role_name": "FileFerryReadOnlyRole"
      }
    },
    "serviceNow": {
      "instance_url": "https://your-instance.service-now.com",
      "username": "api_user",
      "password": "USE_ENV_VARIABLE"
    },
    "notification": {
      "teams_webhook_url": "https://your-webhook-url"
    },
    "monitoring": {
      "datadog_api_key": "USE_ENV_VARIABLE",
      "datadog_app_key": "USE_ENV_VARIABLE"
    }
  }
}
```

### 7. Set Environment Variables

Create `.env` file:

```bash
# ServiceNow
SERVICENOW_USERNAME=api_user
SERVICENOW_PASSWORD=your_secure_password

# Datadog
DATADOG_API_KEY=your_datadog_api_key
DATADOG_APP_KEY=your_datadog_app_key

# FTP/SFTP
SFTP_HOST=your-sftp-server.com
SFTP_USERNAME=sftp_user
SFTP_PASSWORD=sftp_password

FTP_HOST=your-ftp-server.com
FTP_USERNAME=ftp_user
FTP_PASSWORD=ftp_password

# AWS
AWS_DEFAULT_REGION=us-east-1
```

---

## Running the Agent

### Development Mode

```bash
# Start the web API server
python -m src.api.web_api

# Or using uvicorn directly
uvicorn src.api.web_api:app --reload --host 0.0.0.0 --port 8000
```

Access the web interface at: http://localhost:8000

### Production Deployment

#### Option 1: AWS Lambda + API Gateway

```bash
# Package for Lambda
pip install -r requirements.txt -t ./package
cd package
zip -r ../fileferry-agent.zip .
cd ..
zip -g fileferry-agent.zip -r src/

# Deploy using AWS CLI
aws lambda create-function \
    --function-name FileFerryAgent \
    --runtime python3.9 \
    --role arn:aws:iam::ACCOUNT:role/FileFerryAgentRole \
    --handler src.handlers.lambda_handler.handler \
    --zip-file fileb://fileferry-agent.zip \
    --timeout 900 \
    --memory-size 512
```

#### Option 2: AWS ECS/Fargate

```bash
# Build Docker image
docker build -t fileferry-agent:latest .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker tag fileferry-agent:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/fileferry-agent:latest
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/fileferry-agent:latest

# Deploy to ECS (use provided CloudFormation/Terraform)
```

#### Option 3: EC2 Instance

```bash
# On EC2 instance
git clone <repository>
cd fileferry-agent

# Install dependencies
pip install -r requirements.txt

# Run with systemd
sudo cp deployment/fileferry-agent.service /etc/systemd/system/
sudo systemctl enable fileferry-agent
sudo systemctl start fileferry-agent
```

---

## Usage

### Web Interface

1. Navigate to http://your-server:8000
2. Fill in the form:
   - Environment (dev/staging/prod)
   - S3 bucket name
   - AWS region
   - Assignment group
   - File name
   - Destination type (SFTP/FTP)
   - Your email
3. Click "Start Transfer"
4. Receive confirmation with ticket numbers
5. Get Teams notification when complete

### API Usage

```bash
# Start a transfer
curl -X POST http://localhost:8000/api/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "prod",
    "bucket_name": "my-bucket",
    "region": "us-east-1",
    "assignment_group": "IT-Operations",
    "file_name": "data/large-file.csv",
    "destination_type": "sftp",
    "user_email": "user@company.com"
  }'

# Check transfer status
curl http://localhost:8000/api/transfer/{transfer_id}

# Health check
curl http://localhost:8000/api/health
```

---

## Monitoring

### Datadog Dashboard

Key metrics automatically tracked:
- `fileferry.transfer.started`
- `fileferry.transfer.completed`
- `fileferry.transfer.failed`
- `fileferry.transfer.duration`
- `fileferry.sso_login_success`
- `fileferry.sso_auto_logout`

Create dashboard at: https://app.datadoghq.com/dashboard

### ServiceNow Tickets

Two tickets created per transfer:
1. **User Ticket**: Customer-facing, tracks request
2. **Assignment Ticket**: Internal audit trail

### Teams Notifications

Automatic notifications sent for:
- Transfer success (with details)
- Transfer failure (with error)
- Large file warnings

---

## Security Best Practices

1. **Never commit secrets** - Use environment variables
2. **Rotate credentials** - Update passwords quarterly
3. **Monitor SSO sessions** - Review Datadog logs
4. **Audit S3 access** - Enable CloudTrail
5. **Restrict IAM roles** - Read-only S3 access only
6. **Use VPC endpoints** - For private S3 access
7. **Enable MFA** - For AWS console access

---

## Troubleshooting

### Common Issues

#### SSO Authentication Fails
```bash
# Test AWS credentials
aws sts get-caller-identity

# Verify role assumption
aws sts assume-role --role-arn arn:aws:iam::ACCOUNT:role/FileFerryReadOnlyRole --role-session-name test
```

#### ServiceNow API Errors
- Verify instance URL format
- Check API user permissions
- Test with curl:
  ```bash
  curl -u username:password https://instance.service-now.com/api/now/v2/table/incident?sysparm_limit=1
  ```

#### File Transfer Fails
- Check FTP/SFTP credentials
- Verify network connectivity
- Test manual connection:
  ```bash
  sftp username@hostname
  ```

#### Datadog Not Receiving Metrics
- Verify API keys
- Check StatsD agent:
  ```bash
  sudo systemctl status datadog-agent
  ```

---

## Performance Optimization

### For Large Files (> 1 GB)

1. Enable compression in config:
   ```json
   "fileTransfer": {
     "enableCompression": true,
     "chunkSize": 67108864  // 64 MB
   }
   ```

2. Increase Lambda timeout:
   ```json
   "lambda": {
     "timeout": 900,
     "memorySize": 1024
   }
   ```

3. Use parallel streams (implemented automatically)

---

## Maintenance

### Regular Tasks

**Weekly**:
- Review Datadog metrics
- Check ServiceNow ticket backlog
- Monitor error logs

**Monthly**:
- Update dependencies: `pip install --upgrade -r requirements.txt`
- Review AWS costs
- Audit transfer success rates

**Quarterly**:
- Rotate credentials
- Review and update IAM policies
- Performance optimization review

---

## Support

For issues or questions:
1. Check Datadog logs
2. Review ServiceNow tickets
3. Check application logs: `./logs/fileferry.log`
4. Contact DevOps team

---

## License

Proprietary - Internal Use Only
