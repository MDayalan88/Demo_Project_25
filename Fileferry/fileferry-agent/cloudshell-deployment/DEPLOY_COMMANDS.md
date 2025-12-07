# AWS CloudShell Deployment Commands

**You've uploaded the files to AWS CloudShell. Now run these commands INSIDE CloudShell:**

---

## Step 1: Verify Files Are Uploaded

```bash
# List uploaded files
ls -lah

# Should see:
# deploy-phase3.ps1
# step_functions_state_machine.json
# requirements.txt
# lambda_functions/ (folder)

# Check lambda functions
ls -lah lambda_functions/
# Should see 8 .py files
```

---

## Step 2: Install PowerShell (if not already installed)

```bash
# Install PowerShell 7
sudo yum install -y \
  https://github.com/PowerShell/PowerShell/releases/download/v7.4.0/powershell-7.4.0-1.rh.x86_64.rpm

# Verify installation
pwsh --version
```

---

## Step 3: Run Deployment Script

```bash
# Run the deployment
pwsh ./deploy-phase3.ps1 -Region us-east-1 -AccountId 637423332185
```

**This will:**
- ✅ Create 2 IAM roles (Lambda + Step Functions)
- ✅ Package all 8 Lambda functions as ZIP files
- ✅ Deploy all 8 Lambda functions to AWS
- ✅ Create Step Functions state machine
- ✅ Configure all integrations

**Expected time**: 30-45 minutes

---

## Step 4: Monitor Progress

You'll see output like:
```
✅ Checking AWS credentials...
✅ Account: 637423332185, Region: us-east-1
✅ Creating IAM role: FileFerryLambdaExecutionRole...
✅ IAM role created successfully
✅ Creating IAM role: FileFerryStepFunctionsRole...
✅ IAM role created successfully
✅ Packaging Lambda function 1/8: validate_input...
✅ Deploying Lambda function: FileFerry-ValidateInput...
... (continues for all 8)
✅ Creating Step Functions state machine...
✅ Deployment complete!
```

---

## Step 5: Save the Output

At the end, you'll see:
```
========================================
Deployment Summary
========================================

Lambda Functions Deployed (8):
  ✅ FileFerry-ValidateInput
  ✅ FileFerry-AuthSSO
  ✅ FileFerry-DownloadS3
  ✅ FileFerry-TransferFTP
  ✅ FileFerry-ChunkedTransfer
  ✅ FileFerry-UpdateServiceNow
  ✅ FileFerry-NotifyUser
  ✅ FileFerry-Cleanup

Step Functions State Machine:
  ✅ FileFerry-TransferStateMachine
  ARN: arn:aws:states:us-east-1:637423332185:stateMachine:FileFerry-TransferStateMachine

========================================
Next Steps:
1. Update config.yaml with State Machine ARN
2. Test Lambda functions individually
3. Test Step Functions execution
========================================
```

**IMPORTANT**: Copy the State Machine ARN!

---

## Alternative: If PowerShell Doesn't Work

If PowerShell installation fails, use AWS CLI commands directly:

### Create IAM Roles

```bash
# Create Lambda execution role
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
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-role-policy \
  --role-name FileFerryLambdaExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

# Create Step Functions role
aws iam create-role \
  --role-name FileFerryStepFunctionsRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "states.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy \
  --role-name FileFerryStepFunctionsRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaRole
```

### Deploy Lambda Functions

```bash
# Navigate to lambda_functions folder
cd lambda_functions

# Package and deploy each function
for func in validate_input auth_sso download_s3 transfer_ftp chunked_transfer update_servicenow notify_user cleanup; do
  echo "Deploying $func..."
  
  # Create ZIP
  zip ${func}.zip ${func}.py
  
  # Deploy
  aws lambda create-function \
    --function-name FileFerry-$(echo $func | sed 's/_/-/g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2))} 1') \
    --runtime python3.11 \
    --role arn:aws:iam::637423332185:role/FileFerryLambdaExecutionRole \
    --handler ${func}.lambda_handler \
    --zip-file fileb://${func}.zip \
    --timeout 300 \
    --memory-size 512 \
    --environment Variables={DYNAMODB_TABLE_PREFIX=FileFerry-}
done

cd ..
```

### Create Step Functions State Machine

```bash
# Create state machine
aws stepfunctions create-state-machine \
  --name FileFerry-TransferStateMachine \
  --definition file://step_functions_state_machine.json \
  --role-arn arn:aws:iam::637423332185:role/FileFerryStepFunctionsRole
```

---

## Verify Deployment

```bash
# List Lambda functions
aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `FileFerry-`)].FunctionName' \
  --output table

# List Step Functions
aws stepfunctions list-state-machines \
  --query 'stateMachines[?starts_with(name, `FileFerry-`)].{Name:name,ARN:stateMachineArn}' \
  --output table
```

---

## Troubleshooting

### Issue: "Permission denied"
```bash
# Check current user
aws sts get-caller-identity

# Should show account: 637423332185
```

### Issue: "Role does not exist"
```bash
# Wait 10 seconds for IAM role propagation
sleep 10

# Or check if role exists
aws iam get-role --role-name FileFerryLambdaExecutionRole
```

### Issue: "File not found"
```bash
# Check current directory
pwd
ls -lah

# Make sure you're in the folder with deploy-phase3.ps1
```

---

## After Deployment

1. **Copy State Machine ARN** from output
2. **Go back to your laptop**
3. **Update config.yaml**:
   ```yaml
   step_functions:
     state_machine_arn: "arn:aws:states:us-east-1:637423332185:stateMachine:FileFerry-TransferStateMachine"
   ```

4. **Test in AWS Console**:
   - Lambda: https://console.aws.amazon.com/lambda
   - Step Functions: https://console.aws.amazon.com/states

---

## Quick Start Command (All-in-One)

If you want to run everything at once:

```bash
# Install PowerShell and run deployment
sudo yum install -y https://github.com/PowerShell/PowerShell/releases/download/v7.4.0/powershell-7.4.0-1.rh.x86_64.rpm && \
pwsh ./deploy-phase3.ps1 -Region us-east-1 -AccountId 637423332185
```

---

**Run these commands inside AWS CloudShell (browser-based terminal)**

**Status**: Ready to deploy! 🚀
