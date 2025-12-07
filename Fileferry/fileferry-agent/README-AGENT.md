# FileFerry AI Agent

🚀 **Intelligent file transfer orchestration powered by AWS Bedrock Claude Sonnet 4.5**

FileFerry is an AI-powered agent that automates S3-to-FTP/SFTP file transfers with natural language interface, ServiceNow integration, and intelligent decision-making.

## 🌟 Key Features

- **🤖 AI-Powered**: AWS Bedrock Claude Sonnet 4.5 for natural language understanding
- **💬 Teams Bot**: Microsoft Teams integration with Adaptive Cards
- **🔒 Secure**: AWS IAM SSO with 10-second auto-logout
- **🎫 Compliance**: Dual ServiceNow tickets (user + audit) for every transfer
- **📊 Intelligent**: Predictive analytics based on historical transfer data
- **⚡ Optimized**: Automatic transfer strategy selection (direct/parallel/compressed)
- **📈 Observable**: Full AWS X-Ray tracing and CloudWatch logging

## 🏗️ Architecture

```
┌─────────────┐
│ Teams User  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Gateway    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Lambda Handler │─────▶│ Bedrock AI   │
│  (Python 3.11)  │      │ Claude 3.5   │
└────────┬────────┘      └──────────────┘
         │
         ├──────────────┐
         │              │
         ▼              ▼
┌─────────────┐  ┌────────────┐
│  DynamoDB   │  │   Step     │
│  5 Tables   │  │ Functions  │
└─────────────┘  └────────────┘
         │              │
         │              ▼
         │      ┌──────────────┐
         └─────▶│ ServiceNow   │
                │   Tickets    │
                └──────────────┘
```

## 📦 Project Structure

```
fileferry-agent/
├── src/
│   ├── ai_agent/
│   │   ├── bedrock_agent.py      # Main AI orchestrator
│   │   └── agent_tools.py         # 9 tool implementations
│   ├── teams_bot/
│   │   ├── bot_handler.py         # Teams Bot handler
│   │   └── adaptive_cards.py      # Adaptive Card templates
│   ├── handlers/
│   │   ├── sso_handler.py         # SSO authentication
│   │   ├── servicenow_handler.py  # ServiceNow integration
│   │   └── transfer_handler.py    # Transfer execution
│   ├── storage/
│   │   └── dynamodb_manager.py    # DynamoDB operations
│   ├── utils/
│   │   ├── logger.py              # Structured logging
│   │   └── config_loader.py       # Configuration management
│   └── lambda_functions/
│       └── api_handler.py         # Lambda entry point
├── config/
│   └── config.yaml                # Main configuration
├── infrastructure/
│   ├── create_dynamodb_tables.py  # DynamoDB setup
│   └── step_functions_state_machine.json
├── requirements.txt               # Python dependencies
└── .env.example                   # Environment variables template
```

## 🚀 Quick Start

### Prerequisites

- AWS Account with Bedrock access
- Python 3.11+
- AWS CLI configured
- Microsoft Teams Bot registered

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Create DynamoDB Tables

```bash
python infrastructure/create_dynamodb_tables.py us-east-1
```

### 4. Deploy Lambda Function

```bash
# Package dependencies
pip install -r requirements.txt -t package/
cp -r src package/
cd package && zip -r ../fileferry-agent.zip . && cd ..

# Deploy to AWS Lambda
aws lambda create-function \
  --function-name FileFerry-Agent \
  --runtime python3.11 \
  --handler src.lambda_functions.api_handler.lambda_handler \
  --zip-file fileb://fileferry-agent.zip \
  --role arn:aws:iam::ACCOUNT_ID:role/FileFerryLambdaRole \
  --timeout 300 \
  --memory-size 512 \
  --environment Variables="{CONFIG_PATH=config/config.yaml}"
```

### 5. Test the Agent

**Via Teams Bot:**
```
"List my S3 buckets"
"Transfer file data.csv from bucket my-bucket to SFTP server ftp.example.com"
"Show my transfer history"
```

**Via API:**
```bash
curl -X POST https://your-api-gateway-url/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "List my S3 buckets in us-east-1"
  }'
```

## 🗄️ DynamoDB Tables

| Table | Partition Key | Sort Key | TTL | Purpose |
|-------|--------------|----------|-----|---------|
| TransferRequests | userId | requestId | - | Transfer history |
| AgentLearning | transferType | timestamp | 1 year | ML training data |
| UserContext | userId | - | - | User preferences |
| ActiveSessions | sessionId | - | 1 hour | SSO sessions |
| S3FileCache | bucketName | fileKey | 24 hours | S3 metadata cache |

## 🛠️ Available Tools

The AI agent has access to 9 tools:

1. **list_s3_buckets** - List accessible S3 buckets
2. **list_bucket_contents** - List objects in bucket
3. **get_file_metadata** - Get file details (cached 24h)
4. **validate_user_access** - Verify read permissions
5. **analyze_transfer_request** - Recommend transfer strategy
6. **predict_transfer_outcome** - Predict success rate
7. **create_servicenow_tickets** - Create dual tickets
8. **execute_transfer** - Initiate transfer
9. **get_transfer_history** - Retrieve past transfers

## 💰 Cost Analysis

**Monthly Costs (100 transfers/day):**
- Bedrock Claude: $300-600
- Lambda: $20-50
- DynamoDB: $8
- Step Functions: $25
- API Gateway: $3
- S3/Data Transfer: $150-200
- Teams Bot: $0 (using Azure Bot Service free tier)

**Total: $535-1,040/month ($6,420-12,480/year)**

**ROI: 79-89% savings vs. $60,000/year manual process**

## 🔐 Security

- ✅ Read-only S3 access via IAM policies
- ✅ 10-second SSO auto-logout enforced
- ✅ Dual ServiceNow tickets for audit trail
- ✅ All credentials in AWS Secrets Manager
- ✅ X-Ray tracing for observability
- ✅ CloudWatch logging (no PII)

## 📊 Monitoring

**CloudWatch Logs Insights Queries:**

```sql
# High latency requests
fields @timestamp, message
| filter message like /High latency detected/
| sort @timestamp desc

# Failed transfers
fields @timestamp, level, message
| filter level = "ERROR" and message like /transfer/
| sort @timestamp desc
```

**X-Ray Traces:**
- View in AWS Console → X-Ray → Traces
- Filter by execution time, errors, or specific operations

## 🤝 Contributing

This is an internal project. For questions or improvements, contact the DataOps team.

## 📄 License

Proprietary - Internal use only

## 🆘 Support

- **Slack**: #fileferry-support
- **Email**: dataops@company.com
- **ServiceNow**: Create incident with category "FileFerry"

---

**Built with ❤️ by DataOps Team**
