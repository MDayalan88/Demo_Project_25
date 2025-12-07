# 🚀 AWS CloudShell Deployment - Step-by-Step Guide

**Easy deployment without installing AWS CLI on your laptop!**

---

## 📦 Files Ready for Upload

I've created a deployment package in: `cloudshell-deployment/`

**Files included** (11 files):
- ✅ `deploy-phase3.ps1` - Main deployment script
- ✅ `step_functions_state_machine.json` - State machine definition
- ✅ `requirements.txt` - Python dependencies
- ✅ `lambda_functions/` folder with 8 Lambda functions:
  - validate_input.py
  - auth_sso.py
  - download_s3.py
  - transfer_ftp.py
  - chunked_transfer.py
  - update_servicenow.py
  - notify_user.py
  - cleanup.py

---

## 🎯 Step-by-Step Instructions

### Step 1: Login to AWS Console

1. Open your browser
2. Go to: **https://console.aws.amazon.com**
3. Login with your AWS credentials for account: **637423332185**
4. Select region: **US East (N. Virginia) - us-east-1**

---

### Step 2: Open CloudShell

**Option A: Click the icon**
- Look for the **CloudShell icon** (>_) in the top-right corner of AWS Console
- It's next to the notifications bell icon
- Click it to open CloudShell terminal

**Option B: Search for CloudShell**
- Click the search bar at the top
- Type: `CloudShell`
- Click on "CloudShell" service

**CloudShell will open in a new panel at the bottom of your browser.**

---

### Step 3: Create Deployment Folder in CloudShell

In the CloudShell terminal, type:

```bash
mkdir fileferry-deployment
cd fileferry-deployment
```

---

### Step 4: Upload Files to CloudShell

**Method 1: Upload via CloudShell UI (Recommended)**

1. In CloudShell, click **Actions** menu (top-right of terminal)
2. Select **Upload file**
3. Upload these files **one by one**:
   - `deploy-phase3.ps1`
   - `step_functions_state_machine.json`
   - `requirements.txt`

4. Create lambda_functions folder:
   ```bash
   mkdir lambda_functions
   cd lambda_functions
   ```

5. Upload all 8 Python files from `cloudshell-deployment/lambda_functions/`:
   - Use **Actions > Upload file** again
   - Upload each .py file:
     - validate_input.py
     - auth_sso.py
     - download_s3.py
     - transfer_ftp.py
     - chunked_transfer.py
     - update_servicenow.py
     - notify_user.py
     - cleanup.py

6. Go back to deployment folder:
   ```bash
   cd ..
   ```

**Method 2: Upload ZIP file (Faster)**

1. On your laptop, create ZIP file:
   ```powershell
   # In your PowerShell terminal
   Compress-Archive -Path ".\cloudshell-deployment\*" -DestinationPath ".\cloudshell-deployment.zip"
   ```

2. In CloudShell, click **Actions > Upload file**
3. Upload `cloudshell-deployment.zip`
4. Unzip in CloudShell:
   ```bash
   unzip cloudshell-deployment.zip -d fileferry-deployment
   cd fileferry-deployment
   ```

---

### Step 5: Install PowerShell in CloudShell

CloudShell uses Linux (Amazon Linux 2), so we need to install PowerShell:

```bash
# Install PowerShell
sudo yum install -y \
  https://github.com/PowerShell/PowerShell/releases/download/v7.4.0/powershell-7.4.0-1.rh.x86_64.rpm

# Verify installation
pwsh --version
```

**Expected output**: `PowerShell 7.4.0` or similar

---

### Step 6: Verify Files Are Uploaded

```bash
# List all files
ls -lah

# Should see:
# deploy-phase3.ps1
# step_functions_state_machine.json
# requirements.txt
# lambda_functions/

# Check lambda functions
ls -lah lambda_functions/

# Should see 8 .py files
```

---

### Step 7: Run Deployment Script

**Option A: Using PowerShell (Recommended)**

```bash
# Run the deployment script
pwsh ./deploy-phase3.ps1 -Region us-east-1 -AccountId 637423332185
```

**Option B: Convert to Bash (if PowerShell installation fails)**

If PowerShell doesn't work, I can help you convert the script to bash commands.

---

### Step 8: Monitor Deployment Progress

The script will show progress:

```
✅ Checking AWS credentials...
✅ Creating IAM role: FileFerryLambdaExecutionRole...
✅ Creating IAM role: FileFerryStepFunctionsRole...
✅ Packaging Lambda function 1/8: FileFerry-ValidateInput...
✅ Deploying Lambda function: FileFerry-ValidateInput...
✅ Packaging Lambda function 2/8: FileFerry-AuthSSO...
... (continues for all 8 functions)
✅ Creating Step Functions state machine...
✅ Deployment complete!
```

**Expected time**: 30-45 minutes

---

### Step 9: Copy State Machine ARN

After deployment completes, you'll see output like:

```
State Machine ARN: arn:aws:states:us-east-1:637423332185:stateMachine:FileFerry-TransferStateMachine
```

**Copy this ARN** - you'll need it for config.yaml

---

### Step 10: Verify Deployment

**Check Lambda Functions**:
```bash
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `FileFerry-`)].FunctionName'
```

Should show 8 functions:
- FileFerry-ValidateInput
- FileFerry-AuthSSO
- FileFerry-DownloadS3
- FileFerry-TransferFTP
- FileFerry-ChunkedTransfer
- FileFerry-UpdateServiceNow
- FileFerry-NotifyUser
- FileFerry-Cleanup

**Check Step Functions**:
```bash
aws stepfunctions list-state-machines --query 'stateMachines[?starts_with(name, `FileFerry-`)].name'
```

Should show:
- FileFerry-TransferStateMachine

---

### Step 11: Update config.yaml (Back on Your Laptop)

Update your `config/config.yaml` file:

```yaml
step_functions:
  state_machine_arn: "arn:aws:states:us-east-1:637423332185:stateMachine:FileFerry-TransferStateMachine"
```

---

## ✅ Post-Deployment Testing

### Test Lambda Function Individually

1. Go to AWS Console: https://console.aws.amazon.com/lambda
2. Click on `FileFerry-ValidateInput`
3. Go to **Test** tab
4. Create test event with:
   ```json
   {
     "transfer_request_id": "test-123",
     "source_bucket": "your-test-bucket",
     "source_key": "test-file.txt",
     "destination_ftp": {
       "host": "ftp.example.com",
       "port": 21,
       "username": "testuser"
     },
     "servicenow_tickets": {
       "user_ticket": "INC0010001",
       "audit_ticket": "INC0010002"
     }
   }
   ```
5. Click **Test**
6. Check execution results

### Test Step Functions Workflow

1. Go to AWS Console: https://console.aws.amazon.com/states
2. Click on `FileFerry-TransferStateMachine`
3. Click **Start execution**
4. Input test JSON:
   ```json
   {
     "transfer_request_id": "test-transfer-001",
     "user_id": "test-user",
     "source_bucket": "your-s3-bucket",
     "source_key": "test-file.txt",
     "destination_ftp": {
       "host": "ftp.example.com",
       "port": 21,
       "protocol": "ftp",
       "username": "testuser",
       "password": "testpass",
       "path": "/uploads"
     },
     "servicenow_tickets": {
       "user_ticket": "INC0010002",
       "audit_ticket": "INC0010003"
     }
   }
   ```
5. Click **Start execution**
6. Monitor execution graph

---

## 🔧 Troubleshooting

### Issue: "Permission denied" when uploading files
**Solution**: Make sure you're in CloudShell, not your local terminal

### Issue: "pwsh: command not found"
**Solution**: 
```bash
# Check if PowerShell installed
which pwsh

# If not, install again
sudo yum install -y powershell
```

### Issue: "Access Denied" during deployment
**Solution**: 
```bash
# Check AWS credentials
aws sts get-caller-identity

# Should show account: 637423332185
```

### Issue: Lambda deployment fails
**Solution**:
```bash
# Check if zip files created
ls -lah *.zip

# Manually create zip for one Lambda
cd lambda_functions
zip -r ../validate_input.zip validate_input.py
cd ..

# Deploy manually
aws lambda create-function \
  --function-name FileFerry-ValidateInput \
  --runtime python3.11 \
  --role arn:aws:iam::637423332185:role/FileFerryLambdaExecutionRole \
  --handler validate_input.lambda_handler \
  --zip-file fileb://validate_input.zip \
  --timeout 30 \
  --memory-size 128
```

---

## 📊 Deployment Checklist

- [ ] Login to AWS Console (account: 637423332185, region: us-east-1)
- [ ] Open CloudShell
- [ ] Create `fileferry-deployment` folder
- [ ] Upload all files from `cloudshell-deployment/`
- [ ] Install PowerShell in CloudShell
- [ ] Verify all files uploaded (11 files total)
- [ ] Run `deploy-phase3.ps1` script
- [ ] Wait for deployment (30-45 minutes)
- [ ] Copy State Machine ARN
- [ ] Verify 8 Lambda functions created
- [ ] Verify Step Functions state machine created
- [ ] Update config.yaml with State Machine ARN
- [ ] Test Lambda function individually
- [ ] Test Step Functions execution

---

## 🎉 Success Indicators

You'll know deployment succeeded when:

✅ Script shows: "✅ Deployment complete!"
✅ 8 Lambda functions visible in AWS Console
✅ 1 Step Functions state machine visible
✅ No error messages in CloudShell output
✅ State Machine ARN copied successfully

---

## 💡 Pro Tips

1. **Keep CloudShell open** during deployment - don't close browser tab
2. **CloudShell session timeout**: 20 minutes of inactivity closes session
3. **Files persist**: Uploaded files stay in CloudShell for future use
4. **Use screen/tmux**: For long deployments, use `screen` to prevent interruption:
   ```bash
   # Start screen session
   screen -S deployment
   
   # Run deployment
   pwsh ./deploy-phase3.ps1 -Region us-east-1 -AccountId 637423332185
   
   # Detach: Press Ctrl+A, then D
   # Reattach later: screen -r deployment
   ```

---

## 📞 Need Help?

If deployment fails or you have questions:

1. **Check CloudWatch Logs**: 
   - Go to CloudWatch Console
   - Look for error messages

2. **Review deployment script output**:
   - Copy any error messages
   - Look for failed steps

3. **Manual deployment**:
   - If script fails, I can provide manual AWS CLI commands

---

**Location of files to upload**: 
`C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\cloudshell-deployment\`

**Ready to deploy!** 🚀

---

**Last Updated**: December 3, 2025  
**Deployment Method**: AWS CloudShell (No local AWS CLI needed)
