# FileFerry AI Agent - Architecture & Service Details

**Document Version**: 1.0  
**Last Updated**: December 4, 2025  
**Project**: FileFerry - Intelligent File Transfer Orchestration System

---

## 🏗️ Architecture Overview

FileFerry is a **Hybrid AI Agent + Automation Platform** that combines artificial intelligence with serverless cloud infrastructure to orchestrate secure, intelligent file transfers from AWS S3 to FTP/SFTP servers.

### **Architecture Type**: Event-Driven Serverless Microservices

### **Key Characteristics**:
- ✅ Serverless (pay-per-use, auto-scaling)
- ✅ AI-powered decision making (AWS Bedrock Claude 3.5 Sonnet)
- ✅ Event-driven workflows (Step Functions)
- ✅ Zero-trust security (SSO, read-only S3)
- ✅ Real-time monitoring (CloudWatch, X-Ray)
- ✅ Compliance-first (dual ServiceNow ticketing)

---

## 📊 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                          │
├─────────────────────────────────────────────────────────────────────────┤
│  Web UI (demo.html)          Microsoft Teams          Slack             │
│  - HTML/JS/Tailwind          - Adaptive Cards         - Slash Commands  │
│  - 1TB file visualization    - Bot Framework          - Webhooks        │
│  - Real-time progress        - Proactive messages     - Notifications   │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY LAYER                              │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐          ┌─────────────────────┐              │
│  │   REST API Gateway  │          │  WebSocket API      │              │
│  ├─────────────────────┤          ├─────────────────────┤              │
│  │ • Authentication    │          │ • Real-time updates │              │
│  │ • Rate Limiting     │          │ • Connection mgmt   │              │
│  │ • CORS Config       │          │ • Progress stream   │              │
│  │ • JWT Validation    │          │ • Event broadcasting│              │
│  └─────────────────────┘          └─────────────────────┘              │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        COMPUTE & AI LAYER                               │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    AWS Lambda Functions (8)                       │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ 1. ValidateInput      │  5. UpdateServiceNow                     │  │
│  │ 2. AuthSSO            │  6. NotifyUser                           │  │
│  │ 3. DownloadS3         │  7. Cleanup                              │  │
│  │ 4. TransferFTP        │  8. API Handler                          │  │
│  │ [ChunkedTransfer for 1TB+ files]                                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              AWS Bedrock (AI Decision Engine)                     │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │  Model: Claude 3.5 Sonnet v2                                     │  │
│  │  • Natural language understanding                                │  │
│  │  • Context-aware decision making                                 │  │
│  │  • Tool orchestration (9 tools)                                  │  │
│  │  • Transfer strategy optimization                                │  │
│  │  • ML-based outcome prediction                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │           AWS Step Functions (Workflow State Machine)            │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │  11 States:                                                       │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │  │
│  │  │ ValidateInput   │→ │ AuthenticateSSO │→ │ DownloadFromS3  │ │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘ │  │
│  │           │                                                       │  │
│  │           ▼                                                       │  │
│  │  ┌─────────────────┐                                             │  │
│  │  │ CheckFileSize   │                                             │  │
│  │  └─────────────────┘                                             │  │
│  │     │           │                                                 │  │
│  │  <100MB      >100MB                                              │  │
│  │     │           │                                                 │  │
│  │     ▼           ▼                                                 │  │
│  │ ┌────────┐  ┌──────────────┐                                    │  │
│  │ │ Direct │  │ Parallel     │ (Chunked + Multi-stream)          │  │
│  │ │Transfer│  │ Transfer     │                                    │  │
│  │ └────────┘  └──────────────┘                                    │  │
│  │     │           │                                                 │  │
│  │     └─────┬─────┘                                                │  │
│  │           ▼                                                       │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │  │
│  │  │UpdateServiceNow │→ │CleanupAndLogout │→ │StoreOutcome     │ │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘ │  │
│  │           │                                                       │  │
│  │           ▼                                                       │  │
│  │  ┌─────────────────┐          ┌─────────────────┐               │  │
│  │  │SendNotification │          │ HandleError     │ (On failure)  │  │
│  │  └─────────────────┘          └─────────────────┘               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         STORAGE LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                  DynamoDB Tables (5 Tables)                       │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │ 1. TransferRequests    │ Complete transfer audit trail          │  │
│  │    PK: transferId      │ GSI: userId, status, timestamp         │  │
│  │                                                                   │  │
│  │ 2. AgentLearning       │ ML predictions from past transfers     │  │
│  │    PK: transferType    │ TTL: 1 year, learns patterns           │  │
│  │                                                                   │  │
│  │ 3. UserContext         │ Conversation history (10 exchanges)    │  │
│  │    PK: userId          │ TTL: 30 days inactive                  │  │
│  │                                                                   │  │
│  │ 4. ActiveSessions      │ SSO session management                 │  │
│  │    PK: sessionId       │ TTL: 1 hour, 10-sec auto-logout       │  │
│  │                                                                   │  │
│  │ 5. S3FileCache         │ File metadata caching                  │  │
│  │    PK: bucketName+key  │ TTL: 24 hours                          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                         AWS S3                                    │  │
│  ├──────────────────────────────────────────────────────────────────┤  │
│  │  • Source file storage (read-only access)                        │  │
│  │  • Supports 1TB+ files                                           │  │
│  │  • Encryption at rest (AES-256)                                  │  │
│  │  • Versioning enabled                                            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      SECURITY & IDENTITY LAYER                          │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌───────────────┐  │
│  │   AWS SSO/STS       │  │  IAM Roles/Policies │  │ Secrets Mgr   │  │
│  ├─────────────────────┤  ├─────────────────────┤  ├───────────────┤  │
│  │ • 10-sec sessions   │  │ • Least privilege   │  │ • JWT secrets │  │
│  │ • Auto-logout       │  │ • S3 read-only      │  │ • ServiceNow  │  │
│  │ • Temp credentials  │  │ • Cross-service     │  │ • API keys    │  │
│  │ • MFA support       │  │ • Resource ARNs     │  │ • Rotation    │  │
│  └─────────────────────┘  └─────────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   MONITORING & OBSERVABILITY LAYER                      │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌───────────────┐  │
│  │   CloudWatch        │  │    AWS X-Ray        │  │  CloudTrail   │  │
│  ├─────────────────────┤  ├─────────────────────┤  ├───────────────┤  │
│  │ • Logs aggregation  │  │ • Distributed trace │  │ • Audit logs  │  │
│  │ • Custom dashboards │  │ • Service map       │  │ • Compliance  │  │
│  │ • Alarms & alerts   │  │ • Latency analysis  │  │ • Security    │  │
│  │ • Metrics (KPIs)    │  │ • Bottleneck ID     │  │ • Governance  │  │
│  └─────────────────────┘  └─────────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      INTEGRATION LAYER                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  ┌───────┐ │
│  │   ServiceNow    │  │ Microsoft Teams │  │   Datadog   │  │ Slack │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤  ├───────┤ │
│  │• Dual ticketing │  │• Adaptive Cards │  │• Monitoring │  │• Alerts│ │
│  │• INC + RITM     │  │• Bot Framework  │  │• APM        │  │• Notify│ │
│  │• Status updates │  │• Notifications  │  │• Dashboards │  │• Cmds │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  └───────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        DESTINATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────┤
│  FTP/SFTP Servers (Customer-owned)                                     │
│  • Paramiko for SFTP                                                    │
│  • PyFTP for FTP                                                        │
│  • Chunked transfer for 1TB+ files                                     │
│  • Parallel streaming (multiple connections)                           │
│  • Automatic retry with exponential backoff                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Detailed Service Breakdown

### **1. AWS Bedrock (AI Engine)**

**Service Type**: Managed AI/ML Service  
**Model**: Claude 3.5 Sonnet v2 (`anthropic.claude-3-5-sonnet-20241022-v2:0`)  
**Region**: us-east-1

**Configuration**:
```json
{
  "modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0",
  "maxTokens": 4096,
  "temperature": 0.7,
  "topP": 0.9
}
```

**Capabilities**:
- Natural language understanding for user requests
- Context-aware decision making (9 tools available)
- Transfer strategy optimization (direct vs chunked)
- ML-based transfer outcome prediction
- Conversation management (max 10 exchanges)

**Tools Available to AI Agent**:
1. `list_s3_buckets` - List accessible buckets
2. `list_bucket_contents` - List files in bucket
3. `get_file_metadata` - Get file details (cached 24h)
4. `validate_user_access` - Check permissions
5. `analyze_transfer_request` - Determine optimal strategy
6. `predict_transfer_outcome` - ML prediction from history
7. `create_servicenow_tickets` - Create dual tickets
8. `execute_transfer` - Start Step Functions workflow
9. `get_transfer_history` - Query past transfers

**Cost**: Pay-per-token (input + output)  
**Performance**: ~2-5 seconds response time  
**Error Handling**: 3 retries with exponential backoff

---

### **2. AWS Lambda Functions (Compute Layer)**

**Service Type**: Serverless Compute  
**Runtime**: Python 3.11  
**Total Functions**: 8

#### **Function Details**:

| Function Name | Memory | Timeout | Purpose | Triggers |
|--------------|--------|---------|---------|----------|
| **FileFerry-ValidateInput** | 512 MB | 30s | Validate transfer request parameters | Step Functions, API Gateway |
| **FileFerry-AuthSSO** | 512 MB | 30s | AWS SSO authentication, 10-sec sessions | Step Functions |
| **FileFerry-DownloadS3** | 1024 MB | 300s | Download files from S3 (read-only) | Step Functions |
| **FileFerry-TransferFTP** | 1024 MB | 900s | Transfer to FTP/SFTP servers | Step Functions |
| **FileFerry-ChunkedTransfer** | 2048 MB | 900s | Handle 1TB+ files with chunking | Step Functions |
| **FileFerry-UpdateServiceNow** | 512 MB | 60s | Create/update ServiceNow tickets | Step Functions, API Gateway |
| **FileFerry-NotifyUser** | 512 MB | 30s | Send Teams/Slack notifications | Step Functions, EventBridge |
| **FileFerry-Cleanup** | 256 MB | 60s | Cleanup temp files, logout SSO | Step Functions |

**Common Configuration**:
```python
# Environment Variables (all functions)
ENVIRONMENT=production
AWS_REGION=us-east-1
DYNAMODB_TABLE_PREFIX=FileFerry-
LOG_LEVEL=INFO
XRAY_ENABLED=true

# Specific to S3 functions
S3_READ_ONLY_POLICY=enabled
S3_MAX_FILE_SIZE=1TB

# Specific to FTP functions
FTP_CHUNK_SIZE=100MB
FTP_PARALLEL_STREAMS=5
FTP_RETRY_ATTEMPTS=3
```

**IAM Permissions** (per function):
- DynamoDB: GetItem, PutItem, UpdateItem, Query
- S3: GetObject, ListBucket (read-only)
- Bedrock: InvokeModel
- CloudWatch: PutLogEvents
- X-Ray: PutTraceSegments
- Secrets Manager: GetSecretValue

**Deployment Status**: 1/8 deployed (FileFerry-ValidateInput only)

---

### **3. AWS API Gateway (Entry Point)**

**Service Type**: Managed API Service  
**Protocols**: REST (HTTP) + WebSocket

#### **REST API Endpoints**:

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| POST | `/api/login` | JWT token generation | No (credentials) |
| POST | `/api/transfer` | Initiate file transfer | Yes (JWT) |
| GET | `/api/transfer/{id}` | Get transfer status | Yes (JWT) |
| GET | `/api/buckets` | List S3 buckets | Yes (JWT) |
| GET | `/api/buckets/{name}/files` | List bucket files | Yes (JWT) |
| POST | `/api/servicenow/ticket` | Create ticket | Yes (JWT) |
| GET | `/api/history` | Transfer history | Yes (JWT) |
| GET | `/api/health` | Health check | No |

**Configuration**:
```json
{
  "cors": {
    "allowOrigins": ["https://yourdomain.com"],
    "allowMethods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allowHeaders": ["Content-Type", "Authorization"],
    "maxAge": 3600
  },
  "rateLimiting": {
    "rateLimit": 100,
    "burstLimit": 50,
    "period": "minute"
  },
  "authentication": {
    "type": "JWT",
    "algorithm": "HS256",
    "expiry": 3600
  }
}
```

#### **WebSocket API**:

**Endpoint**: `wss://your-api-id.execute-api.us-east-1.amazonaws.com/production`

**Routes**:
- `$connect` - Connection establishment
- `$disconnect` - Connection cleanup
- `subscribe` - Subscribe to transfer updates
- `unsubscribe` - Unsubscribe from updates

**Real-Time Events**:
```json
{
  "type": "progress",
  "transferId": "uuid",
  "percentage": 45,
  "status": "transferring",
  "bytesTransferred": "450GB",
  "estimatedTimeRemaining": "1h 30m"
}
```

**Status**: Not deployed (planned for Week 1, Day 3-4)

---

### **4. AWS Step Functions (Workflow Orchestration)**

**Service Type**: Serverless Workflow Orchestration  
**State Machine Name**: `FileFerry-Transfer-Workflow`  
**States**: 11

#### **Workflow Definition**:

```yaml
States:
  1. ValidateInput:
     Type: Task
     Resource: arn:aws:lambda:*:function:FileFerry-ValidateInput
     Next: AuthenticateSSO
     
  2. AuthenticateSSO:
     Type: Task
     Resource: arn:aws:lambda:*:function:FileFerry-AuthSSO
     Next: DownloadFromS3
     
  3. DownloadFromS3:
     Type: Task
     Resource: arn:aws:lambda:*:function:FileFerry-DownloadS3
     Next: CheckFileSize
     
  4. CheckFileSize:
     Type: Choice
     Choices:
       - Variable: $.fileSize
         NumericLessThan: 104857600  # 100MB
         Next: DirectTransfer
       - Variable: $.fileSize
         NumericGreaterThanEquals: 104857600
         Next: ParallelTransfer
         
  5. DirectTransfer:
     Type: Task
     Resource: arn:aws:lambda:*:function:FileFerry-TransferFTP
     Next: UpdateServiceNowTicket
     
  6. ParallelTransfer:
     Type: Task
     Resource: arn:aws:lambda:*:function:FileFerry-ChunkedTransfer
     Next: UpdateServiceNowTicket
     
  7. UpdateServiceNowTicket:
     Type: Task
     Resource: arn:aws:lambda:*:function:FileFerry-UpdateServiceNow
     Next: CleanupAndLogout
     
  8. CleanupAndLogout:
     Type: Task
     Resource: arn:aws:lambda:*:function:FileFerry-Cleanup
     Next: StoreOutcome
     
  9. StoreOutcome:
     Type: Task
     Resource: arn:aws:dynamodb:*:table:FileFerry-AgentLearning
     Next: SendNotification
     
  10. SendNotification:
      Type: Task
      Resource: arn:aws:lambda:*:function:FileFerry-NotifyUser
      End: true
      
  11. HandleError:
      Type: Task
      Resource: arn:aws:lambda:*:function:FileFerry-NotifyUser
      Parameters:
        errorType: "TransferFailure"
      End: true
```

**Execution Time**:
- Small files (<100MB): 2-5 minutes
- Large files (1TB): 2-3 hours (1 Gbps network)

**Cost**: $0.025 per 1,000 state transitions  
**Status**: JSON defined, not deployed

---

### **5. Amazon DynamoDB (Data Storage)**

**Service Type**: NoSQL Database  
**Capacity Mode**: On-Demand (auto-scaling)  
**Total Tables**: 5

#### **Table Schemas**:

**Table 1: TransferRequests**
```json
{
  "TableName": "FileFerry-TransferRequests",
  "KeySchema": [
    {"AttributeName": "transferId", "KeyType": "HASH"}
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "UserIdIndex",
      "KeySchema": [
        {"AttributeName": "userId", "KeyType": "HASH"},
        {"AttributeName": "timestamp", "KeyType": "RANGE"}
      ]
    },
    {
      "IndexName": "StatusIndex",
      "KeySchema": [
        {"AttributeName": "status", "KeyType": "HASH"},
        {"AttributeName": "timestamp", "KeyType": "RANGE"}
      ]
    }
  ],
  "Attributes": {
    "transferId": "String (UUID)",
    "userId": "String",
    "sourceBucket": "String",
    "sourceKey": "String",
    "destinationServer": "String",
    "fileSize": "Number",
    "status": "String (pending|in-progress|completed|failed)",
    "startTime": "Number (timestamp)",
    "endTime": "Number (timestamp)",
    "duration": "Number (seconds)",
    "serviceNowTickets": ["INC0010001", "RITM0010002"],
    "errorMessage": "String (optional)"
  }
}
```

**Table 2: AgentLearning**
```json
{
  "TableName": "FileFerry-AgentLearning",
  "KeySchema": [
    {"AttributeName": "transferType", "KeyType": "HASH"},
    {"AttributeName": "timestamp", "KeyType": "RANGE"}
  ],
  "TTL": {
    "AttributeName": "expirationTime",
    "Enabled": true,
    "TTLSeconds": 31536000  // 1 year
  },
  "Attributes": {
    "transferType": "String (small|medium|large)",
    "timestamp": "Number",
    "successRate": "Number (0-100)",
    "avgDuration": "Number (seconds)",
    "commonErrors": ["Array of error patterns"],
    "recommendations": "String"
  }
}
```

**Table 3: UserContext**
```json
{
  "TableName": "FileFerry-UserContext",
  "KeySchema": [
    {"AttributeName": "userId", "KeyType": "HASH"}
  ],
  "TTL": {
    "AttributeName": "expirationTime",
    "Enabled": true,
    "TTLSeconds": 2592000  // 30 days inactive
  },
  "Attributes": {
    "userId": "String",
    "conversationHistory": [
      {"role": "user", "content": "...", "timestamp": "..."},
      {"role": "assistant", "content": "...", "timestamp": "..."}
    ],
    "preferences": {
      "defaultRegion": "us-east-1",
      "notificationPreference": "teams"
    },
    "lastInteraction": "Number (timestamp)"
  }
}
```

**Table 4: ActiveSessions**
```json
{
  "TableName": "FileFerry-ActiveSessions",
  "KeySchema": [
    {"AttributeName": "sessionId", "KeyType": "HASH"}
  ],
  "TTL": {
    "AttributeName": "expirationTime",
    "Enabled": true,
    "TTLSeconds": 3600  // 1 hour
  },
  "Attributes": {
    "sessionId": "String (UUID)",
    "userId": "String",
    "ssoToken": "String (encrypted)",
    "createdAt": "Number (timestamp)",
    "lastActivity": "Number (timestamp)",
    "autoLogoutAt": "Number (timestamp + 10 seconds)"
  }
}
```

**Table 5: S3FileCache**
```json
{
  "TableName": "FileFerry-S3FileCache",
  "KeySchema": [
    {"AttributeName": "cacheKey", "KeyType": "HASH"}
  ],
  "TTL": {
    "AttributeName": "expirationTime",
    "Enabled": true,
    "TTLSeconds": 86400  // 24 hours
  },
  "Attributes": {
    "cacheKey": "String (bucketName#fileKey)",
    "bucketName": "String",
    "fileKey": "String",
    "fileSize": "Number",
    "lastModified": "String",
    "contentType": "String",
    "metadata": "Map"
  }
}
```

**Status**: All 5 tables created ✅

---

### **6. AWS S3 (Source File Storage)**

**Service Type**: Object Storage  
**Purpose**: Source files for transfer (read-only)

**Configuration**:
```json
{
  "encryption": {
    "type": "AES-256",
    "atRest": true
  },
  "versioning": {
    "enabled": true
  },
  "lifecycle": {
    "rules": [
      {
        "id": "ArchiveOldFiles",
        "status": "Enabled",
        "transitions": [
          {"days": 90, "storageClass": "GLACIER"}
        ]
      }
    ]
  },
  "accessControl": {
    "policy": "ReadOnlyAccess",
    "blockPublicAccess": true
  }
}
```

**IAM Policy (Read-Only)**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket",
        "s3:GetObjectMetadata"
      ],
      "Resource": [
        "arn:aws:s3:::*",
        "arn:aws:s3:::*/*"
      ]
    },
    {
      "Effect": "Deny",
      "Action": [
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "*"
    }
  ]
}
```

**Support**: Files up to 5TB per object  
**Transfer Acceleration**: Enabled for faster downloads

---

### **7. AWS SSO/STS (Authentication)**

**Service Type**: Identity Management  
**Session Duration**: 10 seconds (auto-logout)

**Configuration**:
```json
{
  "sessionDuration": 10,
  "autoLogout": true,
  "mfaRequired": false,
  "roleArn": "arn:aws:iam::*:role/FileFerry-SSO-Role",
  "region": "us-east-1"
}
```

**Temporary Credentials**:
```python
# Example STS AssumeRole
{
  "AccessKeyId": "ASIA...",
  "SecretAccessKey": "***",
  "SessionToken": "***",
  "Expiration": "2025-12-04T10:00:10Z"  # 10 seconds
}
```

**Security Features**:
- Temporary credentials (no permanent keys)
- Automatic expiration after 10 seconds
- No credential storage in code or logs
- Integrated with CloudTrail for audit

---

### **8. CloudWatch (Monitoring & Logging)**

**Service Type**: Monitoring & Observability

**Log Groups**:
- `/aws/lambda/FileFerry-*` (8 Lambda functions)
- `/aws/apigateway/FileFerry-API`
- `/aws/states/FileFerry-Transfer-Workflow`

**Custom Metrics**:
```json
{
  "namespace": "FileFerry",
  "metrics": [
    {
      "name": "TransferSuccessRate",
      "unit": "Percent",
      "dimensions": ["Environment", "Region"]
    },
    {
      "name": "TransferDuration",
      "unit": "Seconds",
      "dimensions": ["FileSize", "Environment"]
    },
    {
      "name": "APILatency",
      "unit": "Milliseconds",
      "dimensions": ["Endpoint", "StatusCode"]
    },
    {
      "name": "LambdaErrors",
      "unit": "Count",
      "dimensions": ["FunctionName"]
    }
  ]
}
```

**Alarms Configured**:
- Lambda error rate > 5%
- API Gateway 5xx errors > 10 in 1 minute
- Step Functions execution failed > 3 in 5 minutes
- Transfer timeout > 900 seconds

**Status**: Logging enabled, dashboards pending

---

### **9. AWS X-Ray (Distributed Tracing)**

**Service Type**: Application Performance Monitoring

**Tracing Coverage**:
- All Lambda functions (via SDK decorator)
- API Gateway requests
- Step Functions executions
- DynamoDB operations
- Bedrock API calls

**Sample Trace**:
```
API Gateway → Lambda (ValidateInput) → Step Functions → Lambda (AuthSSO) 
→ Lambda (DownloadS3) → Lambda (TransferFTP) → DynamoDB (Update) 
→ Lambda (NotifyUser) → Teams API
```

**Metrics Tracked**:
- End-to-end latency
- Service-to-service latency
- Error rates by service
- Bottleneck identification

**Status**: Code instrumented, not deployed

---

### **10. Secrets Manager & Parameter Store**

**Service Type**: Secure Configuration Management

**Secrets Stored**:
```bash
# JWT Secret
FileFerry/JWT-Secret

# ServiceNow Credentials
FileFerry/ServiceNow
  - instance_url
  - username
  - password

# Microsoft Teams
FileFerry/Teams
  - webhook_url
  - bot_app_id
  - bot_app_password

# Slack
FileFerry/Slack
  - webhook_url
  - bot_token
```

**Parameters Stored**:
```bash
# Production
/fileferry/prod/api-endpoint
/fileferry/prod/websocket-endpoint
/fileferry/prod/region

# Staging
/fileferry/staging/api-endpoint
/fileferry/staging/websocket-endpoint

# Development
/fileferry/dev/api-endpoint
/fileferry/dev/websocket-endpoint
```

**Rotation**: Automatic rotation every 90 days

---

## 🔐 Security Architecture

### **Security Layers**:

1. **Network Security**
   - VPC for FTP Lambda functions
   - Security groups with minimal port access
   - No public IP addresses
   - NAT Gateway for outbound traffic

2. **Identity & Access Management**
   - Least privilege IAM policies
   - Resource-specific ARNs (no wildcards)
   - S3 read-only enforcement
   - MFA for production access

3. **Data Security**
   - S3 encryption at rest (AES-256)
   - TLS 1.2+ for data in transit
   - No credentials in code/logs
   - Secrets rotation every 90 days

4. **Application Security**
   - JWT authentication (1-hour expiry)
   - API rate limiting (100 req/min)
   - Input validation on all endpoints
   - CORS restrictions

5. **Audit & Compliance**
   - CloudTrail logging enabled
   - Dual ServiceNow tickets (user + audit)
   - X-Ray tracing for all requests
   - 30-day log retention

---

## 📊 Performance Specifications

### **Throughput**:
- API requests: 100 req/min per user
- Concurrent transfers: 50 (Lambda concurrency limit)
- S3 download: 1 Gbps (with Transfer Acceleration)
- FTP upload: Depends on destination server

### **Latency**:
- API response time (p95): < 500ms
- Bedrock AI decision: 2-5 seconds
- Transfer initiation: < 10 seconds
- Real-time WebSocket updates: < 1 second

### **Availability**:
- Target: 99.9% (SLA)
- Multi-AZ deployment
- Automatic failover
- Health checks every 30 seconds

### **Scalability**:
- Auto-scaling: Lambda (up to 1000 concurrent)
- DynamoDB: On-demand (auto-scaling)
- API Gateway: No limit (with rate limiting)
- Step Functions: 1 million executions/month

---

## 💰 Cost Estimation (Monthly)

**Assumptions**: 1,000 transfers/month, avg 500GB per transfer

| Service | Usage | Cost |
|---------|-------|------|
| AWS Lambda (8 functions) | 8,000 invocations, 512MB avg | $5 |
| API Gateway | 10,000 requests | $0.035 |
| Step Functions | 1,000 executions | $0.025 |
| DynamoDB (On-Demand) | 10,000 reads, 5,000 writes | $2.50 |
| S3 Transfer Acceleration | 500TB data transfer | $100 |
| Bedrock (Claude 3.5) | 1,000 requests, 1M tokens | $30 |
| CloudWatch | 5GB logs | $2.50 |
| X-Ray | 100,000 traces | $0.50 |
| **Total Estimated** | | **~$140/month** |

**Note**: Actual costs vary based on usage patterns

---

## 🎯 Success Metrics (KPIs)

1. **Transfer Success Rate**: > 98%
2. **Average Transfer Time (1TB)**: < 3 hours
3. **API Availability**: > 99.9%
4. **User Satisfaction**: > 4.5/5
5. **Lambda Error Rate**: < 1%
6. **ServiceNow Ticket Accuracy**: 100%

---

## 📞 Support & Operations

**24/7 Monitoring**: CloudWatch + PagerDuty  
**Incident Response Time**: < 15 minutes  
**Backup & Recovery**: Automated daily backups  
**Disaster Recovery**: Multi-region failover (future)

---

**Document Maintained By**: FileFerry DevOps Team  
**Last Architecture Review**: December 4, 2025  
**Next Review**: January 2026
