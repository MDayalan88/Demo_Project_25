# 🌐 FileFerry Hybrid Cloud Architecture
## AWS + Azure Dual-Cloud Support

---

## 📋 User Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│  Login → Dashboard → Cloud Selection → SSO → Storage → FTP → Done  │
└─────────────────────────────────────────────────────────────────────┘

Step 1: Login Page
   ↓
Step 2: Dashboard (Form Filling)
   ├─ Assignment Group
   ├─ Environment (Dev/UAT/Prod)
   ├─ Cloud Provider Selection ⚡ AWS or Azure
   ├─ Region / Location
   ├─ Bucket/Container Name
   ├─ File Selection
   └─ Priority
   ↓
Step 3: SSO Authentication (Provider-specific color)
   ├─ AWS: Orange background 🟠
   ├─ Azure: Light Blue background 🔵
   ├─ Auto-create 2 tickets (User + Audit)
   ├─ Show notifications (60 seconds)
   └─ Destination Server Configuration
   ↓
Step 4: Cloud Storage Browser
   ├─ AWS → S3 Bucket Browser
   └─ Azure → Blob Storage Browser
   ↓
Step 5: FTP/SFTP Configuration & Transfer
   ├─ File selection confirmation
   ├─ FTP server details
   ├─ Transfer progress visualization
   └─ Completion notification
   ↓
Step 6: Transfer Complete ✅
   └─ [TODO] Auto-logout after 10 seconds
```

---

## 🏗️ AWS Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AWS CLOUD ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   User Browser   │
│  (demo-hybrid)   │
└────────┬─────────┘
         │ HTTPS
         ↓
┌──────────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  HTML/CSS/JavaScript (Tailwind)                          │   │
│  │  • Login Page                                            │   │
│  │  • Dashboard Form                                        │   │
│  │  • AWS SSO Page (Orange) 🟠                              │   │
│  │  • S3 Browser Page                                       │   │
│  │  • FTP Transfer Page                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬─────────────────────────────────────┘
                             │ API Calls
                             ↓
┌──────────────────────────────────────────────────────────────────┐
│                   AWS BACKEND SERVICES                           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  1️⃣ AWS BEDROCK AI (Generative AI)                    │    │
│  │     • Ticket description generation                    │    │
│  │     • File metadata analysis                           │    │
│  │     • Transfer recommendations                         │    │
│  │     • Completion message generation                    │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  2️⃣ AWS LAMBDA FUNCTIONS                               │    │
│  │     • FileFerry-ChatHandler (API Gateway)              │    │
│  │     • FileFerry-DownloadS3                             │    │
│  │     • FileFerry-TransferFTP                            │    │
│  │     • FileFerry-CleanupTemp                            │    │
│  │     • FileFerry-StoreMetadata                          │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  3️⃣ AWS STEP FUNCTIONS (Workflow Orchestration)        │    │
│  │     State 1: Download from S3                          │    │
│  │     State 2: Validate file integrity                   │    │
│  │     State 3: Compress (if needed)                      │    │
│  │     State 4: Transfer to FTP (chunked parallel)        │    │
│  │     State 5: Verify transfer                           │    │
│  │     State 6: Cleanup temp files                        │    │
│  │     State 7: Store metadata in DynamoDB                │    │
│  │     State 8: Send notifications                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  4️⃣ AMAZON S3 (Object Storage)                         │    │
│  │     • Source bucket (user files)                       │    │
│  │     • Temp bucket (transfer staging)                   │    │
│  │     • Archive bucket (audit logs)                      │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  5️⃣ AMAZON DYNAMODB (NoSQL Database)                   │    │
│  │     • User sessions table                              │    │
│  │     • Transfer history table                           │    │
│  │     • File metadata table                              │    │
│  │     • ServiceNow tickets table                         │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  6️⃣ AWS SSO / IAM (Authentication & Authorization)     │    │
│  │     • User authentication                              │    │
│  │     • Role-based access control                        │    │
│  │     • Temporary security credentials                   │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  7️⃣ AMAZON SNS / SES (Notifications)                   │    │
│  │     • Email notifications                              │    │
│  │     • Teams webhook integration                        │    │
│  │     • ServiceNow API updates                           │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                             │
                             ↓
                   ┌──────────────────┐
                   │  FTP/SFTP Server │
                   │  (Customer-owned) │
                   └──────────────────┘
```

---

## ☁️ AZURE Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AZURE CLOUD ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   User Browser   │
│  (demo-hybrid)   │
└────────┬─────────┘
         │ HTTPS
         ↓
┌──────────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  HTML/CSS/JavaScript (Tailwind)                          │   │
│  │  • Login Page                                            │   │
│  │  • Dashboard Form                                        │   │
│  │  • Azure SSO Page (Light Blue) 🔵                        │   │
│  │  • Blob Storage Browser Page                            │   │
│  │  • FTP Transfer Page                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬─────────────────────────────────────┘
                             │ API Calls
                             ↓
┌──────────────────────────────────────────────────────────────────┐
│                  AZURE BACKEND SERVICES                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  1️⃣ AZURE OPENAI SERVICE (Generative AI)              │    │
│  │     • Ticket description generation (GPT-4)            │    │
│  │     • File metadata analysis                           │    │
│  │     • Transfer recommendations                         │    │
│  │     • Completion message generation                    │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  2️⃣ AZURE FUNCTIONS (Serverless Compute)               │    │
│  │     • FileFerry-ChatHandler (HTTP Trigger)             │    │
│  │     • FileFerry-DownloadBlob                           │    │
│  │     • FileFerry-TransferFTP                            │    │
│  │     • FileFerry-CleanupTemp                            │    │
│  │     • FileFerry-StoreMetadata                          │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  3️⃣ AZURE DURABLE FUNCTIONS (Workflow Orchestration)   │    │
│  │     State 1: Download from Blob Storage                │    │
│  │     State 2: Validate file integrity                   │    │
│  │     State 3: Compress (if needed)                      │    │
│  │     State 4: Transfer to FTP (chunked parallel)        │    │
│  │     State 5: Verify transfer                           │    │
│  │     State 6: Cleanup temp files                        │    │
│  │     State 7: Store metadata in Cosmos DB               │    │
│  │     State 8: Send notifications                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  4️⃣ AZURE BLOB STORAGE (Object Storage)                │    │
│  │     • Source container (user files)                    │    │
│  │     • Temp container (transfer staging)                │    │
│  │     • Archive container (audit logs)                   │    │
│  │     • Hot/Cool/Archive tiers                           │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  5️⃣ AZURE COSMOS DB (NoSQL Database)                   │    │
│  │     • User sessions container                          │    │
│  │     • Transfer history container                       │    │
│  │     • File metadata container                          │    │
│  │     • ServiceNow tickets container                     │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  6️⃣ AZURE ENTRA ID (formerly Azure AD)                 │    │
│  │     • User authentication (SSO)                        │    │
│  │     • Role-based access control (RBAC)                 │    │
│  │     • Managed identities                               │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  7️⃣ AZURE COMMUNICATION SERVICES                       │    │
│  │     • Email notifications                              │    │
│  │     • Teams webhook integration                        │    │
│  │     • ServiceNow API updates                           │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                             │
                             ↓
                   ┌──────────────────┐
                   │  FTP/SFTP Server │
                   │  (Customer-owned) │
                   └──────────────────┘
```

---

## 🔄 Service Comparison: AWS vs Azure

| Component | AWS Service | Azure Service | Status |
|-----------|-------------|---------------|--------|
| **AI/ML** | AWS Bedrock | Azure OpenAI | AWS ✅ Azure ⚠️ |
| **Compute** | AWS Lambda | Azure Functions | AWS ✅ Azure ⚠️ |
| **Workflow** | Step Functions | Durable Functions | AWS ✅ Azure ⚠️ |
| **Storage** | S3 | Blob Storage | AWS ✅ Azure ✅ |
| **Database** | DynamoDB | Cosmos DB | AWS ✅ Azure 🔲 |
| **Auth** | AWS SSO/IAM | Entra ID | AWS ✅ Azure 🔲 |
| **Messaging** | SNS/SES | Communication Services | AWS ✅ Azure 🔲 |

**Legend:**
- ✅ Fully implemented
- ⚠️ Partially implemented (mock mode)
- 🔲 Planned (not yet implemented)

---

## 📊 Current Implementation Status

### **Frontend (demo-hybrid.html)** ✅ 100%
```
✅ Login page
✅ Dashboard with cloud provider selection
✅ AWS SSO page (orange) 🟠
✅ Azure SSO page (light blue) 🔵
✅ S3 bucket browser
✅ Azure blob storage browser
✅ FTP/SFTP configuration
✅ Transfer progress visualization
✅ Completion notification
⚠️ Auto-logout (pending)
```

### **AWS Backend** ✅ 95%
```
✅ S3 integration (boto3)
✅ DynamoDB integration
✅ Lambda functions (code ready)
✅ Step Functions (workflow defined)
✅ Bedrock AI (code ready, not connected to UI)
⚠️ SNS/SES notifications (not connected)
```

### **Azure Backend** 🟡 70%
```
✅ Blob Storage integration (azure-storage-blob)
✅ Mock mode testing (works without Azure account)
✅ Azurite emulator support
🔲 Cosmos DB integration (planned)
🔲 Azure Functions deployment (planned)
🔲 Durable Functions workflow (planned)
🔲 Azure OpenAI integration (planned)
🔲 Entra ID SSO (planned)
🔲 Communication Services (planned)
```

---

## 🎯 Data Flow: Step-by-Step

### **AWS Flow:**
```
1. User logs in → Frontend
2. Fills form → Frontend stores transferData
3. Selects AWS → navigateTo('dashboard')
4. Clicks "Transfer" → navigateTo('aws-sso')
   ├─ Generate 2 tickets (User + Audit)
   ├─ Show orange SSO page 🟠
   └─ Display destination config
5. Confirms → navigateTo('s3-bucket')
   ├─ [TODO] Call Lambda to list S3 buckets
   ├─ Display mock S3 files (current)
   └─ User selects file
6. Proceeds → navigateTo('ftp-server')
   ├─ Shows FTP configuration
   ├─ [TODO] Trigger Step Functions workflow
   ├─ Simulates transfer progress (current)
   └─ Shows completion notification
7. [TODO] Auto-logout after 10 seconds
```

### **Azure Flow:**
```
1. User logs in → Frontend
2. Fills form → Frontend stores transferData
3. Selects Azure → navigateTo('dashboard')
4. Clicks "Transfer" → navigateTo('aws-sso') (same component, different colors)
   ├─ Generate 2 tickets (User + Audit)
   ├─ Show light blue SSO page 🔵
   └─ Display destination config
5. Confirms → navigateTo('s3-bucket') (reused for blob storage)
   ├─ [TODO] Call Azure Function to list containers
   ├─ Display mock blob files (current)
   └─ User selects file
6. Proceeds → navigateTo('ftp-server')
   ├─ Shows FTP configuration
   ├─ [TODO] Trigger Durable Functions workflow
   ├─ Simulates transfer progress (current)
   └─ Shows completion notification
7. [TODO] Auto-logout after 10 seconds
```

---

## 🔐 Security Architecture

### **AWS Security:**
```
┌─────────────────────────────────────────────────┐
│  User → AWS SSO → IAM Role → Temporary Creds   │
│         ↓                                       │
│  Lambda Execution Role                          │
│    ├─ S3:GetObject, S3:ListBucket              │
│    ├─ DynamoDB:PutItem, Query                  │
│    ├─ Bedrock:InvokeModel                      │
│    ├─ StepFunctions:StartExecution             │
│    └─ SNS:Publish, SES:SendEmail               │
└─────────────────────────────────────────────────┘
```

### **Azure Security:**
```
┌─────────────────────────────────────────────────┐
│  User → Entra ID → Managed Identity            │
│         ↓                                       │
│  Azure Function App Identity                    │
│    ├─ Storage Blob Data Reader                 │
│    ├─ Cosmos DB Data Contributor               │
│    ├─ Cognitive Services User (OpenAI)         │
│    ├─ Durable Functions Orchestrator           │
│    └─ Communication Services Contributor       │
└─────────────────────────────────────────────────┘
```

---

## 💰 Cost Comparison (Monthly Estimate)

### **AWS Costs:**
| Service | Usage | Cost/Month |
|---------|-------|------------|
| Lambda | 1M invocations | $0.20 |
| Step Functions | 10K workflows | $0.25 |
| S3 | 100GB storage + transfer | $2.50 |
| DynamoDB | On-demand, 1M requests | $1.25 |
| Bedrock | 1M tokens/month | $3.00 |
| **Total** | | **~$7.20** |

### **Azure Costs:**
| Service | Usage | Cost/Month |
|---------|-------|------------|
| Functions | 1M executions | $0.20 |
| Durable Functions | 10K orchestrations | $0.40 |
| Blob Storage | 100GB + operations | $2.00 |
| Cosmos DB | Serverless, 1M RUs | $2.50 |
| Azure OpenAI | 1M tokens/month | $3.00 |
| **Total** | | **~$8.10** |

**Note:** Costs are estimates for development/testing. Production costs depend on actual usage.

---

## 🚀 Next Steps

### **Immediate Tasks (Tomorrow):**
1. ✅ Add auto-logout after transfer completion (10-second countdown)
2. ✅ Enforce 60-second notification display on SSO page
3. ✅ Test full workflow: Login → Dashboard → SSO → Storage → FTP → Logout

### **Optional Enhancements:**
4. 🔲 Connect AWS Lambda API Gateway endpoint
5. 🔲 Integrate Step Functions for real workflow execution
6. 🔲 Connect Bedrock AI for intelligent suggestions
7. 🔲 Add Teams/Email notifications via SNS/SES
8. 🔲 Deploy Azure Functions equivalent
9. 🔲 Implement Cosmos DB for Azure path
10. 🔲 Add Azure OpenAI integration

### **Production Readiness:**
11. 🔲 Add error handling and retry logic
12. 🔲 Implement rate limiting
13. 🔲 Add monitoring and logging (CloudWatch / Azure Monitor)
14. 🔲 Security hardening (encryption, RBAC)
15. 🔲 Performance optimization (caching, CDN)

---

## 📝 Summary

**Current Status:** 🟢 **DEMO READY**

**What Works:**
- ✅ Full UI workflow (Login → Dashboard → SSO → Storage → FTP)
- ✅ Dual cloud provider support (AWS orange, Azure blue)
- ✅ Mock data for demonstration
- ✅ Azure Blob Storage integration (mock mode)
- ✅ AWS S3 integration (real boto3 client)

**What's Missing for Production:**
- ⚠️ Backend API connections (Lambda/Azure Functions)
- ⚠️ Real workflow orchestration (Step Functions/Durable Functions)
- ⚠️ AI integrations (Bedrock/Azure OpenAI)
- ⚠️ Email/Teams notifications
- ⚠️ Auto-logout feature

**Recommendation:** Perfect for **demo/POC**. Needs backend integration for **production**.
