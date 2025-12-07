# Phase 2 Infrastructure Setup - COMPLETE ✅

## Overview

Phase 2 infrastructure setup provides the complete DynamoDB architecture and IAM roles required for the FileFerry AI Agent to function.

## Created Infrastructure

### DynamoDB Tables (5 Tables)

#### 1. FileFerry-ActiveSessions
- **Purpose**: SSO session management with 10-second timeout
- **Primary Key**: session_token (String)
- **TTL**: 10 seconds (auto-deletion)
- **Encryption**: KMS
- **Billing**: PAY_PER_REQUEST (on-demand)
- **Attributes**:
  - session_token (PK)
  - user_id
  - servicenow_request_id
  - aws_access_key_id
  - aws_secret_access_key
  - aws_session_token
  - region
  - created_at
  - ttl (10 seconds)

#### 2. FileFerry-UserContext
- **Purpose**: Store conversation history and user context
- **Primary Key**: user_id (String)
- **TTL**: 30 days
- **Encryption**: KMS
- **Billing**: PAY_PER_REQUEST
- **Attributes**:
  - user_id (PK)
  - conversation_history (List)
  - preferences (Map)
  - last_activity
  - created_at
  - ttl (30 days)

#### 3. FileFerry-TransferRequests
- **Purpose**: Track all transfer requests with query capability
- **Primary Key**: transfer_id (String)
- **GSI**: UserIdIndex (user_id + created_at)
- **TTL**: 90 days
- **Encryption**: KMS
- **Billing**: PAY_PER_REQUEST
- **Attributes**:
  - transfer_id (PK)
  - user_id (GSI)
  - created_at (GSI Range Key)
  - source_bucket
  - source_key
  - destination_config
  - status
  - servicenow_user_ticket
  - servicenow_audit_ticket
  - step_functions_arn
  - ttl (90 days)

#### 4. FileFerry-AgentLearning
- **Purpose**: ML predictions and learning data
- **Composite Key**: transfer_type (Hash) + size_category (Range)
- **TTL**: None (permanent storage)
- **Encryption**: KMS
- **Billing**: PAY_PER_REQUEST
- **Attributes**:
  - transfer_type (PK)
  - size_category (SK)
  - total_transfers
  - successful_transfers
  - failed_transfers
  - average_duration
  - success_rate
  - last_updated

#### 5. FileFerry-S3FileCache
- **Purpose**: Cache S3 file metadata for performance
- **Primary Key**: cache_key (String) - format: "bucket#key"
- **TTL**: 24 hours
- **Encryption**: KMS
- **Billing**: PAY_PER_REQUEST
- **Attributes**:
  - cache_key (PK)
  - bucket_name
  - file_key
  - size_bytes
  - last_modified
  - content_type
  - etag
  - metadata (Map)
  - cached_at
  - ttl (24 hours)

### IAM Roles

#### FileFerryReadOnlyRole
- **Purpose**: Assumed by SSO Handler for read-only S3 access
- **Trust Policy**: Lambda service + AWS account with ExternalId
- **Permissions**:
  - ✅ s3:GetObject, s3:ListBucket (read-only)
  - ❌ s3:PutObject, s3:DeleteObject (explicitly denied)
  - ✅ DynamoDB access to all 5 tables
  - ✅ CloudWatch metrics (namespace: FileFerry)
  - ✅ X-Ray tracing

## Deployment Options

### Option 1: Python Script (Recommended)
```bash
cd infrastructure
python create_all_dynamodb_tables.py
```

**Features**:
- Creates all 5 tables
- Enables TTL automatically
- Waits for tables to be ACTIVE
- Verifies all tables created
- Shows summary

### Option 2: PowerShell Setup Script
```powershell
.\setup-phase2-infrastructure.ps1
```

**Features**:
- Full infrastructure setup
- Creates DynamoDB tables
- Creates IAM role
- Verification checks
- Dry-run mode: `.\setup-phase2-infrastructure.ps1 -DryRun`

### Option 3: CloudFormation
```bash
aws cloudformation create-stack \
  --stack-name FileFerry-Infrastructure \
  --template-body file://infrastructure/cloudformation/template.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

**Features**:
- Infrastructure as Code
- Complete stack management
- Automatic rollback on failure
- Stack outputs for integration

### Option 4: AWS CLI (Manual)
```bash
# ActiveSessions table
aws dynamodb create-table \
  --table-name FileFerry-ActiveSessions \
  --attribute-definitions AttributeName=session_token,AttributeType=S \
  --key-schema AttributeName=session_token,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Enable TTL
aws dynamodb update-time-to-live \
  --table-name FileFerry-ActiveSessions \
  --time-to-live-specification Enabled=true,AttributeName=ttl
```

## Configuration Updates Required

### config/config.yaml
```yaml
# Add DynamoDB table names
dynamodb:
  active_sessions_table: "FileFerry-ActiveSessions"
  user_context_table: "FileFerry-UserContext"
  transfer_requests_table: "FileFerry-TransferRequests"
  agent_learning_table: "FileFerry-AgentLearning"
  s3_file_cache_table: "FileFerry-S3FileCache"
  region: "us-east-1"

# Update SSO configuration
sso:
  start_url: "https://your-sso-portal.awsapps.com/start"
  region: "us-east-1"
  account_id: "123456789012"  # Your AWS Account ID
  role_name: "FileFerryReadOnlyRole"
  session_duration: 10  # seconds

# Agent configuration
agent:
  test_mode: false  # Set to true for local development
  model_id: "anthropic.claude-3-5-sonnet-20241022-v2:0"
  max_conversation_exchanges: 10
  region: "us-east-1"
```

## Verification Steps

### 1. Verify Tables Created
```bash
aws dynamodb list-tables --region us-east-1 | grep FileFerry
```

Expected output:
```
FileFerry-ActiveSessions
FileFerry-AgentLearning
FileFerry-S3FileCache
FileFerry-TransferRequests
FileFerry-UserContext
```

### 2. Verify TTL Enabled
```bash
aws dynamodb describe-time-to-live \
  --table-name FileFerry-ActiveSessions \
  --region us-east-1
```

Expected: `TimeToLiveStatus: "ENABLED"`

### 3. Verify IAM Role
```bash
aws iam get-role --role-name FileFerryReadOnlyRole
```

### 4. Test DynamoDB Access
```bash
cd infrastructure
python -c "
import boto3
dynamodb = boto3.client('dynamodb', region_name='us-east-1')
tables = dynamodb.list_tables()
print('Tables:', tables['TableNames'])
"
```

### 5. Test SSO Handler (Integration Test)
```python
# test_sso_integration.py
from src.handlers.sso_handler import SSOHandler
import yaml

# Load config
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

# Initialize SSO Handler
sso = SSOHandler(config)

# Test authentication
try:
    session_token = sso.authenticate_user(
        user_id="test@example.com",
        servicenow_request_id="REQ0010001",
        region="us-east-1"
    )
    print(f"✅ Session created: {session_token}")
    
    # Verify session
    is_valid = sso.is_session_valid(session_token)
    print(f"✅ Session valid: {is_valid}")
    
    # Get credentials
    creds = sso.get_session_credentials(session_token)
    print(f"✅ Credentials retrieved: {creds['region']}")
    
except Exception as e:
    print(f"❌ Error: {e}")
```

## Cost Estimation

### DynamoDB Tables (PAY_PER_REQUEST)
- **Storage**: ~$0.25/GB/month
- **Reads**: $0.25 per million requests
- **Writes**: $1.25 per million requests

**Estimated Monthly Cost** (based on 10,000 transfers/month):
- ActiveSessions: ~$0.10 (high turnover, 10-sec TTL)
- UserContext: ~$1.00 (conversation history)
- TransferRequests: ~$2.00 (main transaction table)
- AgentLearning: ~$0.50 (ML data)
- S3FileCache: ~$0.50 (metadata cache)
- **Total DynamoDB**: ~$4.10/month

### IAM Roles
- **Cost**: FREE (no charge for IAM roles)

### Total Phase 2 Infrastructure
- **~$5/month** (excluding data transfer and Lambda costs)

## Security Features

### Encryption
- ✅ All tables use KMS encryption at rest
- ✅ Data in transit encrypted via TLS

### Access Control
- ✅ IAM role with least privilege (read-only S3)
- ✅ Explicit deny on write operations
- ✅ TTL-based automatic data deletion

### Compliance
- ✅ 10-second SSO timeout (security requirement)
- ✅ Automatic data expiration (GDPR-friendly)
- ✅ Audit trail via DynamoDB (90-day retention)

## Integration Status

### ✅ Ready Components
1. BedrockFileFerryAgent (core AI orchestrator)
2. AgentTools (all 9 tool functions)
3. SSOHandler (10-second timeout)
4. DynamoDB schema (5 tables designed and created)
5. IAM role (read-only enforcement)

### ⏳ Next Phase (Phase 3)
1. ServiceNow Handler - Dual ticket creation
2. Transfer Handler - S3→FTP streaming
3. Step Functions workflow - 6-state orchestration
4. Lambda API handlers - API Gateway integration
5. Frontend updates - Real SSO, S3 browser, config pages

## Troubleshooting

### Table Creation Fails
**Error**: `ResourceInUseException`
- **Cause**: Table already exists
- **Solution**: Use `describe-table` to verify, or delete and recreate

### IAM Role Creation Fails
**Error**: `EntityAlreadyExists`
- **Cause**: Role already exists
- **Solution**: Update existing role or use different name

### TTL Not Enabling
**Error**: `ValidationException`
- **Cause**: Table still creating
- **Solution**: Wait for table status = ACTIVE

### Permission Denied
**Error**: `AccessDeniedException`
- **Cause**: AWS credentials lack permissions
- **Solution**: Attach AdministratorAccess or specific DynamoDB/IAM policies

## Rollback Instructions

### Delete All Tables
```bash
aws dynamodb delete-table --table-name FileFerry-ActiveSessions --region us-east-1
aws dynamodb delete-table --table-name FileFerry-UserContext --region us-east-1
aws dynamodb delete-table --table-name FileFerry-TransferRequests --region us-east-1
aws dynamodb delete-table --table-name FileFerry-AgentLearning --region us-east-1
aws dynamodb delete-table --table-name FileFerry-S3FileCache --region us-east-1
```

### Delete IAM Role
```bash
# Delete inline policy first
aws iam delete-role-policy \
  --role-name FileFerryReadOnlyRole \
  --policy-name FileFerryReadOnlyPolicy

# Delete role
aws iam delete-role --role-name FileFerryReadOnlyRole
```

### CloudFormation Rollback
```bash
aws cloudformation delete-stack --stack-name FileFerry-Infrastructure
```

## Success Metrics

✅ **Infrastructure Created**:
- 5 DynamoDB tables operational
- IAM role with read-only access
- TTL enabled on 4 tables
- GSI configured on TransferRequests
- KMS encryption on all tables

✅ **Integration Points Ready**:
- SSO Handler can authenticate users
- Agent can store conversation history
- Tools can cache S3 metadata
- Transfer tracking database ready
- ML learning data storage ready

✅ **Security Posture**:
- Read-only S3 access enforced
- 10-second session timeout active
- Automatic data deletion via TTL
- Encryption at rest and in transit

## References

- **Architecture**: `ARCHITECTURE_IMPLEMENTATION.md`
- **SSO Handler**: `SSO_HANDLER_COMPLETE.md`
- **Quick Start**: `QUICKSTART_INTEGRATION.md`
- **CloudFormation**: `infrastructure/cloudformation/template.yaml`
- **Python Script**: `infrastructure/create_all_dynamodb_tables.py`
- **IAM Policies**: `infrastructure/iam-policies/`

---

**Phase 2 Status**: ✅ **COMPLETE**
**Created**: December 2025
**Ready for**: Phase 3 (ServiceNow Handler, Transfer Handler, Step Functions)
