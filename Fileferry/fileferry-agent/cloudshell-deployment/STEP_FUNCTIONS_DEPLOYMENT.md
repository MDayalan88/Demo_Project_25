# Step Functions State Machine Deployment

## 📋 Current Status
✅ **All 14 Lambda functions deployed**
🎯 **Next Step: Create Step Functions State Machine**

## 🚀 Quick Deploy in AWS CloudShell

### Option 1: AWS Console (Recommended - 10 minutes)

1. **Go to Step Functions Console**
   ```
   https://us-east-1.console.aws.amazon.com/states/home?region=us-east-1#/statemachines
   ```

2. **Create State Machine**
   - Click "Create state machine"
   - Choose "Write your workflow in code"
   - Definition type: Standard

3. **Paste State Machine Definition**
   - Copy the entire content from `step_functions_complete.json`
   - Paste into the definition editor
   - The definition includes:
     - ✅ ValidateInput → AuthenticateSSO
     - ✅ DownloadFromS3 → CheckFileSize
     - ✅ TransferFTP (small files <1GB)
     - ✅ ChunkedTransfer (large files ≥1GB)
     - ✅ UpdateServiceNow → NotifyUser
     - ✅ Cleanup (error handling)

4. **Configure State Machine**
   - Name: `FileFerry-TransferStateMachine`
   - Permissions: Create new role
   - Role name: `FileFerryStepFunctionsRole`
   - Click "Create state machine"

5. **Verify IAM Permissions**
   The auto-created role should have:
   - Lambda invoke permissions for all FileFerry functions
   - CloudWatch Logs permissions
   - X-Ray tracing (optional)

---

### Option 2: AWS CLI (CloudShell - 5 minutes)

```bash
# Step 1: Get account ID
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export REGION="us-east-1"

# Step 2: Create IAM role for Step Functions
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "states.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
    --role-name FileFerryStepFunctionsRole \
    --assume-role-policy-document file://trust-policy.json

# Step 3: Create IAM policy for Lambda invocation
cat > lambda-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:*:*:function:FileFerry-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
    --role-name FileFerryStepFunctionsRole \
    --policy-name FileFerryStepFunctionsPolicy \
    --policy-document file://lambda-policy.json

# Step 4: Wait for IAM propagation
echo "⏳ Waiting 10 seconds for IAM role to propagate..."
sleep 10

# Step 5: Create Step Functions State Machine
aws stepfunctions create-state-machine \
    --name FileFerry-TransferStateMachine \
    --definition file://step_functions_complete.json \
    --role-arn arn:aws:iam::${ACCOUNT_ID}:role/FileFerryStepFunctionsRole \
    --type STANDARD

echo "✅ Step Functions State Machine created!"
```

---

## 🧪 Test the State Machine

### Test Input (Copy-paste this):
```json
{
  "user_id": "test@example.com",
  "servicenow_tickets": ["INC0010001", "RITM0010001"],
  "s3_bucket": "fileferry-source-bucket",
  "s3_key": "test-file.txt",
  "ftp_host": "ftp.example.com",
  "ftp_user": "testuser",
  "ftp_password": "testpass",
  "ftp_path": "/uploads/test-file.txt",
  "protocol": "sftp"
}
```

### Test Steps:
1. Go to Step Functions Console
2. Select `FileFerry-TransferStateMachine`
3. Click "Start execution"
4. Paste test input above
5. Click "Start execution"
6. Watch the visual workflow progress

---

## 📊 Expected Flow Visualization

```
┌─────────────────┐
│ ValidateInput   │ ← Checks required fields
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AuthenticateSSO │ ← Creates 10-second session
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DownloadFromS3  │ ← Gets S3 metadata
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ CheckFileSize   │ ← Decision: <1GB or ≥1GB?
└────┬──────┬─────┘
     │      │
     │      └─────────────────┐
     │                        │
     ▼                        ▼
┌──────────┐         ┌─────────────────┐
│Transfer  │         │ChunkedTransfer  │
│   FTP    │         │(Parallel chunks)│
└────┬─────┘         └────────┬────────┘
     │                        │
     └──────┬─────────────────┘
            │
            ▼
   ┌─────────────────┐
   │UpdateServiceNow │ ← Updates both tickets
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │  NotifyUser     │ ← Teams/Email notification
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │    Cleanup      │ ← Remove temp files
   └─────────────────┘
```

---

## ⚠️ Cleanup Duplicate Functions (Optional)

You have some duplicate functions with different casing. To clean them up:

```bash
# Delete duplicate functions (keep PascalCase versions)
aws lambda delete-function --function-name FileFerry-AuthSso
aws lambda delete-function --function-name FileFerry-TransferFtp
aws lambda delete-function --function-name FileFerry-UpdateServicenow

# Verify cleanup
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `FileFerry`)].FunctionName' --output table
```

**After cleanup, you should have 11 functions:**
- 8 core transfer functions (PascalCase)
- 3 API Gateway functions

---

## 📈 Progress Update

| Component | Status | Progress |
|-----------|--------|----------|
| **Lambda Functions** | ✅ Complete | 100% (14 deployed) |
| **DynamoDB Tables** | ✅ Complete | 100% (5 tables) |
| **Step Functions** | 🔄 In Progress | 0% (Next step) |
| **API Gateway** | ⏳ Pending | 0% |
| **Frontend Integration** | ⏳ Pending | 0% |
| **Overall** | 🔄 In Progress | **75%** |

---

## 🎯 After Step Functions - Next Steps

1. **Test Step Functions** (15 minutes)
   - Execute with test input
   - Verify all steps complete successfully
   - Check CloudWatch Logs for errors

2. **Create API Gateway** (30 minutes)
   - REST API: FileFerry-API
   - 3 endpoints:
     - POST /transfer/start → Start-Transfer Lambda
     - GET /transfer/status/{id} → Get-Status Lambda
     - GET /transfer/history → Get-History Lambda

3. **Frontend Integration** (1 hour)
   - Update API endpoints in frontend
   - Test end-to-end: UI → API → Step Functions → Lambda
   - Deploy frontend to S3/CloudFront

---

## 🆘 Troubleshooting

### Issue: "Could not assume role"
**Solution**: Wait 30 seconds for IAM propagation, then retry

### Issue: "Lambda function not found"
**Solution**: Verify function names match exactly (case-sensitive):
```bash
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `FileFerry`)].FunctionName'
```

### Issue: "Execution failed"
**Solution**: Check CloudWatch Logs:
```bash
aws logs tail /aws/states/FileFerry-TransferStateMachine --follow
```

---

## ✅ Success Criteria

- [ ] Step Functions State Machine created
- [ ] IAM role has Lambda invoke permissions
- [ ] Test execution completes successfully
- [ ] All 8 Lambda functions invoked in correct order
- [ ] CloudWatch Logs show no errors
- [ ] Visual workflow matches expected flow diagram

**Estimated Time: 10-15 minutes**

**Ready to proceed? Start with Option 1 (AWS Console) for visual feedback!**
