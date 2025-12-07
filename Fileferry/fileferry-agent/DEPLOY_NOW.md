# 🚀 DEPLOY LAMBDA FUNCTIONS NOW - Quick Start Guide

**Current Status**: AWS CLI not installed on local machine  
**Solution**: Use AWS CloudShell (browser-based) OR install AWS CLI locally

---

## ✅ OPTION 1: AWS CLOUDSHELL (RECOMMENDED - NO INSTALLATION NEEDED)

### Step 1: Access AWS CloudShell

1. **Open AWS Console**: https://console.aws.amazon.com
2. **Login** with your credentials
3. **Click CloudShell icon** (terminal icon in top navigation bar)
   - Wait 30 seconds for CloudShell to initialize

### Step 2: Upload Files to CloudShell

```bash
# In CloudShell, create directory
mkdir fileferry-deployment
cd fileferry-deployment
```

**Upload these files** (use CloudShell "Actions" → "Upload file"):
- `deploy-phase3.ps1` → Convert to bash or use manually
- All files from `lambda_functions/` folder:
  - `auth_sso.py`
  - `download_s3.py`
  - `transfer_ftp.py`
  - `chunked_transfer.py`
  - `update_servicenow.py`
  - `notify_user.py`
  - `cleanup.py`

### Step 3: Deploy Using AWS CLI Commands

```bash
# Set your account ID
export ACCOUNT_ID="637423332185"
export REGION="us-east-1"

# Create IAM role for Lambda
aws iam create-role \
    --role-name FileFerryLambdaExecutionRole \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }]
    }'

# Attach policies
aws iam attach-role-policy \
    --role-name FileFerryLambdaExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
    --role-name FileFerryLambdaExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

aws iam attach-role-policy \
    --role-name FileFerryLambdaExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

# Wait for role to propagate
echo "Waiting 10 seconds for IAM role..."
sleep 10

# Deploy Lambda 1: AuthSSO
zip auth_sso.zip auth_sso.py
aws lambda create-function \
    --function-name FileFerry-AuthSSO \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler auth_sso.lambda_handler \
    --zip-file fileb://auth_sso.zip \
    --timeout 30 \
    --memory-size 512 \
    --environment Variables={DYNAMODB_TABLE=FileFerry-ActiveSessions}
echo "✅ FileFerry-AuthSSO deployed"

# Deploy Lambda 2: DownloadS3
zip download_s3.zip download_s3.py
aws lambda create-function \
    --function-name FileFerry-DownloadS3 \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler download_s3.lambda_handler \
    --zip-file fileb://download_s3.zip \
    --timeout 300 \
    --memory-size 1024 \
    --environment Variables={DYNAMODB_CACHE_TABLE=FileFerry-S3FileCache,CACHE_TTL=86400}
echo "✅ FileFerry-DownloadS3 deployed"

# Deploy Lambda 3: TransferFTP
zip transfer_ftp.zip transfer_ftp.py
aws lambda create-function \
    --function-name FileFerry-TransferFTP \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler transfer_ftp.lambda_handler \
    --zip-file fileb://transfer_ftp.zip \
    --timeout 900 \
    --memory-size 1024 \
    --environment Variables={CHUNK_SIZE=10485760,MAX_RETRIES=3}
echo "✅ FileFerry-TransferFTP deployed"

# Deploy Lambda 4: ChunkedTransfer
zip chunked_transfer.zip chunked_transfer.py
aws lambda create-function \
    --function-name FileFerry-ChunkedTransfer \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler chunked_transfer.lambda_handler \
    --zip-file fileb://chunked_transfer.zip \
    --timeout 900 \
    --memory-size 2048 \
    --environment Variables={CHUNK_SIZE=104857600,PARALLEL_CHUNKS=4}
echo "✅ FileFerry-ChunkedTransfer deployed"

# Deploy Lambda 5: UpdateServiceNow
zip update_servicenow.zip update_servicenow.py
aws lambda create-function \
    --function-name FileFerry-UpdateServiceNow \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler update_servicenow.lambda_handler \
    --zip-file fileb://update_servicenow.zip \
    --timeout 60 \
    --memory-size 512 \
    --environment Variables={SERVICENOW_INSTANCE_URL=https://dev329630.service-now.com}
echo "✅ FileFerry-UpdateServiceNow deployed"

# Deploy Lambda 6: NotifyUser
zip notify_user.zip notify_user.py
aws lambda create-function \
    --function-name FileFerry-NotifyUser \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler notify_user.lambda_handler \
    --zip-file fileb://notify_user.zip \
    --timeout 30 \
    --memory-size 512 \
    --environment Variables={DYNAMODB_TABLE=FileFerry-TransferRequests}
echo "✅ FileFerry-NotifyUser deployed"

# Deploy Lambda 7: Cleanup
zip cleanup.zip cleanup.py
aws lambda create-function \
    --function-name FileFerry-Cleanup \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler cleanup.lambda_handler \
    --zip-file fileb://cleanup.zip \
    --timeout 60 \
    --memory-size 256 \
    --environment Variables={DYNAMODB_SESSION_TABLE=FileFerry-ActiveSessions}
echo "✅ FileFerry-Cleanup deployed"

# List all deployed functions
echo ""
echo "======================================"
echo "DEPLOYMENT COMPLETE! Listing functions:"
echo "======================================"
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `FileFerry`)].FunctionName' --output table
```

**Time**: 5-10 minutes in CloudShell

---

## ✅ OPTION 2: AWS CONSOLE (MANUAL - LONGEST BUT MOST VISUAL)

### For Each Function:

1. **Go to**: https://console.aws.amazon.com/lambda
2. **Click**: "Create function"
3. **Select**: "Author from scratch"
4. **Function name**: (e.g., `FileFerry-AuthSSO`)
5. **Runtime**: Python 3.11
6. **Permissions**: Use existing role → `FileFerryLambdaExecutionRole`
   - If role doesn't exist, create it with policies:
     - `AWSLambdaBasicExecutionRole`
     - `AmazonS3ReadOnlyAccess`
     - `AmazonDynamoDBFullAccess`

7. **Upload code**:
   - On your local machine:
     ```powershell
     cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\cloudshell-deployment\lambda_functions
     Compress-Archive -Path auth_sso.py -DestinationPath auth_sso.zip -Force
     ```
   - In AWS Console: Click "Upload from" → ".zip file" → Select `auth_sso.zip`

8. **Configure**:
   - Handler: `auth_sso.lambda_handler`
   - Memory: 512 MB
   - Timeout: 30 seconds
   - Environment variables (see table below)

9. **Test**:
   - Create test event with sample JSON
   - Click "Test"
   - Verify response

### Repeat for all 7 functions:

| Function Name | File | Handler | Memory | Timeout | Env Variables |
|---------------|------|---------|--------|---------|---------------|
| FileFerry-AuthSSO | auth_sso.py | auth_sso.lambda_handler | 512 MB | 30s | DYNAMODB_TABLE=FileFerry-ActiveSessions |
| FileFerry-DownloadS3 | download_s3.py | download_s3.lambda_handler | 1024 MB | 300s | DYNAMODB_CACHE_TABLE=FileFerry-S3FileCache |
| FileFerry-TransferFTP | transfer_ftp.py | transfer_ftp.lambda_handler | 1024 MB | 900s | CHUNK_SIZE=10485760 |
| FileFerry-ChunkedTransfer | chunked_transfer.py | chunked_transfer.lambda_handler | 2048 MB | 900s | CHUNK_SIZE=104857600 |
| FileFerry-UpdateServiceNow | update_servicenow.py | update_servicenow.lambda_handler | 512 MB | 60s | SERVICENOW_INSTANCE_URL=https://dev329630.service-now.com |
| FileFerry-NotifyUser | notify_user.py | notify_user.lambda_handler | 512 MB | 30s | DYNAMODB_TABLE=FileFerry-TransferRequests |
| FileFerry-Cleanup | cleanup.py | cleanup.lambda_handler | 256 MB | 60s | DYNAMODB_SESSION_TABLE=FileFerry-ActiveSessions |

**Time**: 60-90 minutes for all 7 functions

---

## ✅ OPTION 3: INSTALL AWS CLI LOCALLY (ONE-TIME SETUP)

### Step 1: Install AWS CLI

```powershell
# Download AWS CLI installer
Invoke-WebRequest -Uri https://awscli.amazonaws.com/AWSCLIV2.msi -OutFile AWSCLIV2.msi

# Install
Start-Process msiexec.exe -Wait -ArgumentList '/I AWSCLIV2.msi /quiet'

# Verify installation (restart PowerShell first)
aws --version
```

### Step 2: Configure AWS Credentials

```powershell
# Run configuration wizard
aws configure

# Enter your credentials when prompted:
# AWS Access Key ID: [Your access key]
# AWS Secret Access Key: [Your secret key]
# Default region: us-east-1
# Default output format: json
```

### Step 3: Run Deployment Script

```powershell
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\cloudshell-deployment

# Fix script path issue
$content = Get-Content .\deploy-phase3.ps1 -Raw
$content = $content -replace '\\infrastructure\\lambda_functions\\', '\lambda_functions\'
$content | Set-Content .\deploy-phase3.ps1 -Encoding UTF8

# Run deployment
.\deploy-phase3.ps1 -Region "us-east-1" -AccountId "637423332185"
```

**Time**: 30 minutes (15 min install + 15 min deploy)

---

## 🎯 RECOMMENDED APPROACH

**For fastest deployment**: Use **AWS CloudShell (Option 1)**

### Quick Copy-Paste for CloudShell:

```bash
# ONE-LINE DEPLOYMENT SCRIPT (paste in CloudShell)
export ACCOUNT_ID="637423332185" REGION="us-east-1"; \
aws iam create-role --role-name FileFerryLambdaExecutionRole --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' 2>/dev/null; \
aws iam attach-role-policy --role-name FileFerryLambdaExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole; \
aws iam attach-role-policy --role-name FileFerryLambdaExecutionRole --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess; \
aws iam attach-role-policy --role-name FileFerryLambdaExecutionRole --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess; \
sleep 10; \
for func in auth_sso download_s3 transfer_ftp chunked_transfer update_servicenow notify_user cleanup; do \
  zip ${func}.zip ${func}.py; \
  aws lambda create-function --function-name FileFerry-$(echo $func | sed 's/_//g' | sed 's/\(.\)/\U\1/') --runtime python3.11 --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole --handler ${func}.lambda_handler --zip-file fileb://${func}.zip --timeout 300 --memory-size 512; \
  echo "✅ FileFerry-$(echo $func | sed 's/_//g') deployed"; \
done; \
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `FileFerry`)].FunctionName' --output table
```

---

## 📊 DEPLOYMENT PROGRESS TRACKER

After deployment, verify with:

```powershell
# In PowerShell (after installing AWS CLI)
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `FileFerry`)].FunctionName' --output table
```

Or in AWS Console:
- Go to: https://console.aws.amazon.com/lambda
- Filter: "FileFerry"
- Should see: **8 functions total** (including FileFerry-ValidateInput)

---

## ✅ POST-DEPLOYMENT VERIFICATION

### Test FileFerry-AuthSSO

```bash
# In CloudShell or local terminal with AWS CLI
aws lambda invoke \
    --function-name FileFerry-AuthSSO \
    --payload '{"user_id":"test@example.com","servicenow_tickets":["INC0010001"]}' \
    response.json

cat response.json
```

**Expected Output**:
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

## 🚨 TROUBLESHOOTING

### Error: "Role cannot be assumed"
**Solution**: Wait 30 seconds after creating IAM role, then retry.

### Error: "Function already exists"
**Solution**: Function was deployed previously. Use `update-function-code` instead:
```bash
aws lambda update-function-code \
    --function-name FileFerry-AuthSSO \
    --zip-file fileb://auth_sso.zip
```

### Error: "Access Denied"
**Solution**: Your AWS user needs Lambda and IAM permissions. Contact AWS admin.

---

## 📞 SUPPORT

If you encounter issues, check:
1. **IAM Role** exists: `FileFerryLambdaExecutionRole`
2. **DynamoDB Tables** exist: All 5 FileFerry tables ACTIVE
3. **AWS Region** is correct: `us-east-1`
4. **AWS Account ID** is correct: `637423332185`

---

## 🎯 NEXT STEPS AFTER DEPLOYMENT

Once all 7 Lambdas are deployed:

1. ✅ Verify all 8 functions visible in AWS Console
2. ✅ Test each function individually
3. ✅ Create Step Functions State Machine
4. ✅ Create API Gateway
5. ✅ Test end-to-end workflow

**You're on track to 100% completion! 🚀**
