# 🚀 FileFerry - Lambda Functions Deployment Guide

**Date**: December 4, 2025  
**Status**: 7 Lambda Functions Pending Deployment  
**Current**: 1/8 deployed (FileFerry-ValidateInput ✅)

---

## 📊 DEPLOYMENT STATUS

| Lambda Function | Status | Purpose | Memory | Timeout |
|-----------------|--------|---------|--------|---------|
| FileFerry-ValidateInput | ✅ DEPLOYED | Validate transfer requests | 512 MB | 30s |
| FileFerry-AuthSSO | ⏳ PENDING | SSO authentication (10s session) | 512 MB | 30s |
| FileFerry-DownloadS3 | ⏳ PENDING | S3 metadata & download prep | 1024 MB | 300s |
| FileFerry-TransferFTP | ⏳ PENDING | S3→FTP/SFTP streaming | 1024 MB | 900s |
| FileFerry-ChunkedTransfer | ⏳ PENDING | Large file chunked transfer | 2048 MB | 900s |
| FileFerry-UpdateServiceNow | ⏳ PENDING | Update dual tickets | 512 MB | 60s |
| FileFerry-NotifyUser | ⏳ PENDING | Teams/Email notifications | 512 MB | 30s |
| FileFerry-Cleanup | ⏳ PENDING | Session cleanup & temp files | 256 MB | 60s |

---

## 🎯 OPTION 1: AUTOMATED DEPLOYMENT (RECOMMENDED)

### Prerequisites
1. ✅ AWS CLI installed and configured
2. ✅ PowerShell 5.1+ (you have this)
3. ✅ AWS credentials configured
4. ✅ Lambda function code exists

### Step 1: Verify Prerequisites

```powershell
# Navigate to deployment directory
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\cloudshell-deployment

# Check AWS CLI
aws --version

# Check AWS credentials
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "...",
#     "Account": "637423332185",
#     "Arn": "arn:aws:iam::637423332185:user/your-user"
# }
```

### Step 2: Fix Deployment Script Path

**Issue**: Script references `.\infrastructure\lambda_functions\` but files are in `.\lambda_functions\`

Run this to fix:

```powershell
# Open PowerShell as Administrator
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\cloudshell-deployment

# Edit deploy-phase3.ps1 - Replace line 116
# OLD: $functionPath = ".\infrastructure\lambda_functions\$($lambda.File)"
# NEW: $functionPath = ".\lambda_functions\$($lambda.File)"

# Quick fix with PowerShell
$content = Get-Content .\deploy-phase3.ps1 -Raw
$content = $content -replace '\\infrastructure\\lambda_functions\\', '\lambda_functions\'
$content | Set-Content .\deploy-phase3.ps1 -Encoding UTF8
```

### Step 3: Run Deployment Script

```powershell
# Execute deployment (this will take 5-10 minutes)
.\deploy-phase3.ps1 -Region "us-east-1" -AccountId "637423332185"

# Expected output:
# ======================================================================
# FileFerry - Phase 3 Deployment Script
# ======================================================================
# 
# 🔍 Checking AWS CLI...
# ✅ AWS CLI found: aws-cli/2.x.x
# 
# 🔍 Checking AWS credentials...
# ✅ AWS Account: 637423332185
# 
# ======================================================================
# Step 1: Create IAM Role for Lambda Functions
# ======================================================================
# ✅ IAM role created (or already exists)
# 
# ======================================================================
# Step 2: Package and Deploy Lambda Functions
# ======================================================================
# 📦 Deploying: FileFerry-ValidateInput...
# ✅ Deployed: FileFerry-ValidateInput
# 
# 📦 Deploying: FileFerry-AuthSSO...
# ✅ Deployed: FileFerry-AuthSSO
# 
# ... (continues for all 8 functions)
```

### Step 4: Verify Deployment

```powershell
# List all deployed Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `FileFerry`)].FunctionName' --output table

# Expected output:
# -------------------------------
# |       ListFunctions        |
# +-----------------------------+
# |  FileFerry-ValidateInput   |
# |  FileFerry-AuthSSO         |
# |  FileFerry-DownloadS3      |
# |  FileFerry-TransferFTP     |
# |  FileFerry-ChunkedTransfer |
# |  FileFerry-UpdateServiceNow|
# |  FileFerry-NotifyUser      |
# |  FileFerry-Cleanup         |
# +-----------------------------+
```

---

## 🎯 OPTION 2: MANUAL DEPLOYMENT (AWS CONSOLE)

If the automated script fails, use AWS Console:

### Function 1: FileFerry-AuthSSO

1. **Go to AWS Console** → Lambda → Create function
2. **Function name**: `FileFerry-AuthSSO`
3. **Runtime**: Python 3.11
4. **Architecture**: x86_64
5. **Permissions**: Use existing role `FileFerryLambdaExecutionRole`

6. **Upload Code**:
```powershell
# Create ZIP file
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\cloudshell-deployment\lambda_functions
Compress-Archive -Path auth_sso.py -DestinationPath auth_sso.zip -Force
```

7. **In AWS Console**:
   - Click "Upload from" → ".zip file"
   - Select `auth_sso.zip`
   - Handler: `auth_sso.lambda_handler`

8. **Configuration**:
   - Memory: 512 MB
   - Timeout: 30 seconds
   - Environment variables:
     ```
     DYNAMODB_TABLE=FileFerry-ActiveSessions
     SESSION_DURATION=10
     ```

9. **Test**:
```json
{
  "user_id": "test@example.com",
  "servicenow_tickets": ["INC0010001", "INC0010002"]
}
```

**Expected Response**:
```json
{
  "status": "authenticated",
  "session_token": "uuid-here",
  "user_id": "test@example.com",
  "session_duration": 10,
  "expires_at": 1733334567
}
```

---

### Function 2: FileFerry-DownloadS3

1. **Create function**: `FileFerry-DownloadS3`
2. **Runtime**: Python 3.11
3. **Role**: `FileFerryLambdaExecutionRole`

4. **Create ZIP**:
```powershell
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\cloudshell-deployment\lambda_functions
Compress-Archive -Path download_s3.py -DestinationPath download_s3.zip -Force
```

5. **Upload ZIP** → Handler: `download_s3.lambda_handler`

6. **Configuration**:
   - Memory: 1024 MB
   - Timeout: 300 seconds (5 minutes)
   - Environment variables:
     ```
     DYNAMODB_CACHE_TABLE=FileFerry-S3FileCache
     CACHE_TTL=86400
     ```

7. **Test**:
```json
{
  "session_token": "valid-session-token",
  "bucket": "your-bucket-name",
  "file_key": "path/to/file.csv"
}
```

---

### Function 3: FileFerry-TransferFTP

1. **Create function**: `FileFerry-TransferFTP`
2. **Runtime**: Python 3.11
3. **Role**: `FileFerryLambdaExecutionRole`

4. **Dependencies Issue**: This function needs `paramiko` library

**Create Layer for Dependencies**:
```powershell
# Create dependencies package
mkdir lambda_layer
cd lambda_layer
pip install paramiko -t python/
Compress-Archive -Path python -DestinationPath paramiko_layer.zip -Force

# Upload to AWS Lambda Layers
aws lambda publish-layer-version `
    --layer-name FileFerry-ParamikoLayer `
    --description "Paramiko for FTP/SFTP transfers" `
    --zip-file fileb://paramiko_layer.zip `
    --compatible-runtimes python3.11
```

5. **Create ZIP**:
```powershell
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\cloudshell-deployment\lambda_functions
Compress-Archive -Path transfer_ftp.py -DestinationPath transfer_ftp.zip -Force
```

6. **Upload ZIP** → Handler: `transfer_ftp.lambda_handler`

7. **Configuration**:
   - Memory: 1024 MB
   - Timeout: 900 seconds (15 minutes)
   - **Layers**: Add `FileFerry-ParamikoLayer`
   - Environment variables:
     ```
     CHUNK_SIZE=10485760
     MAX_RETRIES=3
     ```

---

### Function 4: FileFerry-ChunkedTransfer

1. **Create function**: `FileFerry-ChunkedTransfer`
2. **Runtime**: Python 3.11
3. **Role**: `FileFerryLambdaExecutionRole`

4. **Create ZIP**:
```powershell
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\cloudshell-deployment\lambda_functions
Compress-Archive -Path chunked_transfer.py -DestinationPath chunked_transfer.zip -Force
```

5. **Upload ZIP** → Handler: `chunked_transfer.lambda_handler`

6. **Configuration**:
   - Memory: 2048 MB (large files need more memory)
   - Timeout: 900 seconds (15 minutes)
   - **Layers**: Add `FileFerry-ParamikoLayer`
   - Environment variables:
     ```
     CHUNK_SIZE=104857600
     PARALLEL_CHUNKS=4
     DYNAMODB_TABLE=FileFerry-TransferRequests
     ```

---

### Function 5: FileFerry-UpdateServiceNow

1. **Create function**: `FileFerry-UpdateServiceNow`
2. **Runtime**: Python 3.11
3. **Role**: `FileFerryLambdaExecutionRole`

4. **Create ZIP**:
```powershell
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\cloudshell-deployment\lambda_functions
Compress-Archive -Path update_servicenow.py -DestinationPath update_servicenow.zip -Force
```

5. **Upload ZIP** → Handler: `update_servicenow.lambda_handler`

6. **Configuration**:
   - Memory: 512 MB
   - Timeout: 60 seconds
   - Environment variables:
     ```
     SERVICENOW_INSTANCE_URL=https://dev329630.service-now.com
     SERVICENOW_USERNAME=admin
     SERVICENOW_PASSWORD=<your-password>
     ```

7. **Test**:
```json
{
  "tickets": ["INC0010001", "INC0010002"],
  "status": "completed",
  "transfer_details": {
    "file_name": "test.csv",
    "size": 150000000,
    "duration": 120
  }
}
```

---

### Function 6: FileFerry-NotifyUser

1. **Create function**: `FileFerry-NotifyUser`
2. **Runtime**: Python 3.11
3. **Role**: `FileFerryLambdaExecutionRole`

4. **Create ZIP**:
```powershell
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\cloudshell-deployment\lambda_functions
Compress-Archive -Path notify_user.py -DestinationPath notify_user.zip -Force
```

5. **Upload ZIP** → Handler: `notify_user.lambda_handler`

6. **Configuration**:
   - Memory: 512 MB
   - Timeout: 30 seconds
   - Environment variables:
     ```
     TEAMS_WEBHOOK_URL=https://your-teams-webhook.com
     DYNAMODB_TABLE=FileFerry-TransferRequests
     ```

---

### Function 7: FileFerry-Cleanup

1. **Create function**: `FileFerry-Cleanup`
2. **Runtime**: Python 3.11
3. **Role**: `FileFerryLambdaExecutionRole`

4. **Create ZIP**:
```powershell
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\cloudshell-deployment\lambda_functions
Compress-Archive -Path cleanup.py -DestinationPath cleanup.zip -Force
```

5. **Upload ZIP** → Handler: `cleanup.lambda_handler`

6. **Configuration**:
   - Memory: 256 MB
   - Timeout: 60 seconds
   - Environment variables:
     ```
     DYNAMODB_SESSION_TABLE=FileFerry-ActiveSessions
     DYNAMODB_CACHE_TABLE=FileFerry-S3FileCache
     ```

---

## 🔧 IAM ROLE REQUIREMENTS

The `FileFerryLambdaExecutionRole` needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:637423332185:table/FileFerry-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectMetadata",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::*",
        "arn:aws:s3:::*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
    },
    {
      "Effect": "Allow",
      "Action": [
        "states:StartExecution"
      ],
      "Resource": "arn:aws:states:us-east-1:637423332185:stateMachine:FileFerry-*"
    }
  ]
}
```

### Create IAM Role (if doesn't exist):

```powershell
# Create trust policy
@"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@ | Out-File -FilePath trust-policy.json -Encoding UTF8

# Create role
aws iam create-role `
    --role-name FileFerryLambdaExecutionRole `
    --assume-role-policy-document file://trust-policy.json

# Attach managed policies
aws iam attach-role-policy `
    --role-name FileFerryLambdaExecutionRole `
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy `
    --role-name FileFerryLambdaExecutionRole `
    --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

aws iam attach-role-policy `
    --role-name FileFerryLambdaExecutionRole `
    --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
```

---

## ✅ POST-DEPLOYMENT VERIFICATION

### Test Each Function

```powershell
# Test FileFerry-AuthSSO
aws lambda invoke `
    --function-name FileFerry-AuthSSO `
    --payload '{"user_id":"test@example.com","servicenow_tickets":["INC0010001"]}' `
    response.json

# Check response
Get-Content response.json | ConvertFrom-Json

# Expected: {"status":"authenticated","session_token":"..."}
```

### Monitor Logs

```powershell
# Get recent logs for a function
aws logs tail /aws/lambda/FileFerry-AuthSSO --follow

# Or in AWS Console:
# CloudWatch → Log groups → /aws/lambda/FileFerry-AuthSSO
```

### Check Function Status

```powershell
# Get all FileFerry functions with status
aws lambda list-functions `
    --query 'Functions[?starts_with(FunctionName, `FileFerry`)].{Name:FunctionName,Runtime:Runtime,Memory:MemorySize,Timeout:Timeout,LastModified:LastModified}' `
    --output table
```

---

## 🚨 TROUBLESHOOTING

### Issue 1: "Role not found"
**Solution**: Wait 10-20 seconds after creating IAM role, then retry.

### Issue 2: "ZIP file too large"
**Solution**: Use Lambda Layers for dependencies like `paramiko`, `boto3`, etc.

### Issue 3: "Environment variable not set"
**Solution**: Update each function with required environment variables in AWS Console.

### Issue 4: "Timeout errors"
**Solution**: Increase timeout (especially for TransferFTP and ChunkedTransfer to 900 seconds).

### Issue 5: "Permission denied to access DynamoDB"
**Solution**: Attach `AmazonDynamoDBFullAccess` policy to `FileFerryLambdaExecutionRole`.

---

## 📊 DEPLOYMENT CHECKLIST

- [ ] AWS CLI installed and configured
- [ ] AWS credentials verified (`aws sts get-caller-identity`)
- [ ] IAM role `FileFerryLambdaExecutionRole` created
- [ ] Fix deployment script path (infrastructure → lambda_functions)
- [ ] Run `.\deploy-phase3.ps1` OR deploy manually
- [ ] Verify all 8 functions visible in AWS Console
- [ ] Test FileFerry-AuthSSO function
- [ ] Test FileFerry-DownloadS3 function
- [ ] Create Paramiko Lambda Layer for FTP functions
- [ ] Configure ServiceNow credentials in environment variables
- [ ] Test end-to-end: ValidateInput → AuthSSO → DownloadS3
- [ ] Check CloudWatch logs for errors
- [ ] Update `config/config.yaml` with Lambda ARNs

---

## ⏱️ ESTIMATED TIME

| Method | Time | Complexity |
|--------|------|------------|
| **Automated Script** | 10-15 minutes | Low (recommended) |
| **Manual AWS Console** | 60-90 minutes | Medium |
| **Troubleshooting** | +30 minutes | Variable |

---

## 🎯 NEXT STEPS AFTER DEPLOYMENT

Once all 7 Lambda functions are deployed:

1. **Create Step Functions State Machine** (links all Lambdas)
2. **Create API Gateway** (provides REST endpoints)
3. **Test end-to-end workflow** (form → SSO → transfer → notification)
4. **Configure monitoring** (CloudWatch dashboards, alarms)

---

## 📞 QUICK START COMMAND

```powershell
# ONE-LINE DEPLOYMENT (use this!)
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\cloudshell-deployment; .\deploy-phase3.ps1 -Region "us-east-1" -AccountId "637423332185"
```

**This will deploy all 7 pending Lambda functions in one go! 🚀**
