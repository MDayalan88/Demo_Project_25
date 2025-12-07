# FileFerry AI Agent - Deployment Guide

## 📋 Prerequisites

1. **AWS Account** with the following services enabled:
   - AWS Bedrock (Claude 3.5 Sonnet model access)
   - Lambda
   - DynamoDB
   - Step Functions
   - API Gateway
   - IAM Identity Center (SSO)
   - CloudWatch
   - X-Ray
   - Secrets Manager

2. **Microsoft Azure** (for Teams Bot):
   - Azure Bot Service registration
   - Teams App registration

3. **ServiceNow Instance**:
   - API credentials
   - Incident table access

4. **Development Tools**:
   - Python 3.11+
   - AWS CLI
   - Git

## 🔧 Step-by-Step Deployment

### 1. Clone and Setup

```bash
cd fileferry-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key, Secret Key, and Region
```

### 3. Create DynamoDB Tables

```bash
python infrastructure/create_dynamodb_tables.py us-east-1
```

**Expected Output:**
```
Creating table FileFerry-TransferRequests...
✅ Table FileFerry-TransferRequests created successfully
Creating table FileFerry-AgentLearning...
✅ Table FileFerry-AgentLearning created successfully
...
🎉 All tables created successfully!
```

### 4. Set Up IAM Roles

**Create Lambda Execution Role:**

```bash
aws iam create-role \
  --role-name FileFerryLambdaRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'
```

**Attach Policies:**

```bash
# Basic Lambda execution
aws iam attach-role-policy \
  --role-name FileFerryLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# X-Ray tracing
aws iam attach-role-policy \
  --role-name FileFerryLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess

# DynamoDB access
aws iam attach-role-policy \
  --role-name FileFerryLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

# Bedrock access
aws iam put-role-policy \
  --role-name FileFerryLambdaRole \
  --policy-name BedrockAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": "*"
    }]
  }'

# Step Functions access
aws iam put-role-policy \
  --role-name FileFerryLambdaRole \
  --policy-name StepFunctionsAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "states:StartExecution",
        "states:DescribeExecution",
        "states:StopExecution"
      ],
      "Resource": "*"
    }]
  }'
```

### 5. Store Secrets in AWS Secrets Manager

```bash
# ServiceNow credentials
aws secretsmanager create-secret \
  --name FileFerry/ServiceNow \
  --secret-string '{
    "instance_url": "https://yourinstance.service-now.com",
    "username": "your_username",
    "password": "your_password"
  }'

# Teams Bot credentials
aws secretsmanager create-secret \
  --name FileFerry/TeamsBot \
  --secret-string '{
    "app_id": "your-teams-app-id",
    "app_password": "your-teams-app-password"
  }'
```

### 6. Update Configuration

Edit `config/config.yaml`:

```yaml
aws:
  region: us-east-1  # Your region

sso:
  start_url: https://your-sso-portal.awsapps.com/start
  account_id: 123456789012  # Your AWS account ID
  role_name: FileFerryReadOnlyRole
```

### 7. Package Lambda Function

```bash
# Create package directory
mkdir -p package

# Install dependencies
pip install -r requirements.txt -t package/

# Copy source code
cp -r src package/
cp -r config package/

# Create deployment package
cd package
zip -r ../fileferry-agent.zip .
cd ..
```

### 8. Deploy Lambda Function

```bash
aws lambda create-function \
  --function-name FileFerry-Agent \
  --runtime python3.11 \
  --handler src.lambda_functions.api_handler.lambda_handler \
  --zip-file fileb://fileferry-agent.zip \
  --role arn:aws:iam::ACCOUNT_ID:role/FileFerryLambdaRole \
  --timeout 300 \
  --memory-size 512 \
  --environment Variables="{
    CONFIG_PATH=config/config.yaml,
    AWS_REGION=us-east-1,
    BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
  }" \
  --tracing-config Mode=Active
```

### 9. Create API Gateway

```bash
# Create REST API
aws apigateway create-rest-api \
  --name FileFerry-API \
  --description "FileFerry AI Agent API"

# Get API ID (replace in commands below)
API_ID=$(aws apigateway get-rest-apis --query "items[?name=='FileFerry-API'].id" --output text)

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --query "items[0].id" --output text)

# Create /api/messages resource (for Teams Bot)
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part api

API_RESOURCE=$(aws apigateway get-resources --rest-api-id $API_ID --query "items[?path=='/api'].id" --output text)

aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $API_RESOURCE \
  --path-part messages

# Create POST method
MESSAGES_RESOURCE=$(aws apigateway get-resources --rest-api-id $API_ID --query "items[?path=='/api/messages'].id" --output text)

aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $MESSAGES_RESOURCE \
  --http-method POST \
  --authorization-type NONE

# Integrate with Lambda
LAMBDA_ARN=$(aws lambda get-function --function-name FileFerry-Agent --query 'Configuration.FunctionArn' --output text)

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $MESSAGES_RESOURCE \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations

# Deploy API
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod
```

### 10. Configure Step Functions

```bash
# Create Step Functions state machine
aws stepfunctions create-state-machine \
  --name FileFerryTransferStateMachine \
  --definition file://infrastructure/step_functions_state_machine.json \
  --role-arn arn:aws:iam::ACCOUNT_ID:role/StepFunctionsRole
```

### 11. Register Microsoft Teams Bot

1. Go to [Azure Portal](https://portal.azure.com)
2. Create **Azure Bot**:
   - Name: FileFerry Bot
   - Messaging endpoint: `https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/api/messages`
3. Create **App Registration**:
   - Copy App ID and create secret
   - Update `.env` with credentials
4. Configure Teams channel
5. Install app in Teams

### 12. Configure SSO (IAM Identity Center)

```bash
# Create read-only role for file transfers
aws iam create-role \
  --role-name FileFerryReadOnlyRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach S3 read-only policy
aws iam attach-role-policy \
  --role-name FileFerryReadOnlyRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

### 13. Test Deployment

**Health Check:**
```bash
curl https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "agent": "FileFerry AI Agent",
  "version": "1.0.0"
}
```

**Test Chat API:**
```bash
curl -X POST https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "Hello FileFerry"
  }'
```

### 14. Monitor Deployment

**CloudWatch Logs:**
```bash
aws logs tail /aws/lambda/FileFerry-Agent --follow
```

**X-Ray Traces:**
```bash
# View in AWS Console
open https://console.aws.amazon.com/xray/home
```

## 🔍 Troubleshooting

### Lambda Timeout
- Increase timeout: `aws lambda update-function-configuration --function-name FileFerry-Agent --timeout 600`

### Bedrock Access Denied
- Verify Bedrock model access in console
- Check IAM role has `bedrock:InvokeModel` permission

### DynamoDB Errors
- Verify tables exist: `aws dynamodb list-tables`
- Check IAM permissions for DynamoDB

### Teams Bot Not Responding
- Verify API Gateway endpoint in Azure Bot configuration
- Check Lambda logs for errors
- Verify Teams Bot credentials in Secrets Manager

## 📊 Post-Deployment Tasks

1. **Enable CloudWatch Alarms:**
   - Lambda errors
   - High latency (>5s)
   - Failed transfers

2. **Set Up Datadog (Optional):**
   - Install Datadog Lambda Layer
   - Configure API key in environment variables

3. **Create ServiceNow Integration:**
   - Test ticket creation
   - Verify assignment group exists

4. **User Training:**
   - Share Teams Bot link
   - Provide example commands
   - Document common workflows

## ✅ Deployment Checklist

- [ ] DynamoDB tables created
- [ ] IAM roles configured
- [ ] Lambda function deployed
- [ ] API Gateway created
- [ ] Step Functions state machine created
- [ ] Secrets stored in Secrets Manager
- [ ] Teams Bot registered
- [ ] SSO configured
- [ ] Health check passing
- [ ] Test transfer completed
- [ ] CloudWatch alarms configured
- [ ] Documentation updated

## 🆘 Support

For deployment issues:
- **Slack**: #fileferry-deployment
- **Email**: devops@company.com
- **Documentation**: [Internal Wiki](https://wiki.company.com/fileferry)

---

**Deployment completed! 🎉**
