# SAM Deployment Guide - FileFerry Phase 3

## Quick Deploy (3-4 minutes)

### Step 1: Upload to CloudShell
Upload these files to CloudShell:
- `template.yaml` (SAM template - just created)
- `step_functions_state_machine.json`
- `lambda_functions/` folder (all 8 .py files)

### Step 2: Run SAM Deploy

```bash
# In CloudShell terminal
cd ~

# Install SAM CLI (if not already installed)
pip install aws-sam-cli --user

# Verify installation
sam --version

# Build the SAM application
sam build

# Deploy with guided prompts (first time)
sam deploy --guided

# Or deploy directly (faster)
sam deploy \
  --stack-name fileferry-stack \
  --capabilities CAPABILITY_IAM \
  --region us-east-1 \
  --resolve-s3 \
  --no-confirm-changeset

# Get State Machine ARN from output
aws cloudformation describe-stacks \
  --stack-name fileferry-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' \
  --output text
```

## What SAM Does:
1. ✅ Packages all Lambda functions
2. ✅ Creates S3 bucket for deployment artifacts
3. ✅ Deploys all 8 Lambda functions in parallel
4. ✅ Creates Step Functions state machine
5. ✅ Returns State Machine ARN immediately
6. ✅ Handles IAM permissions automatically

## Expected Output:
```
CloudFormation stack changeset
---------------------------------------------------------
Operation          LogicalResourceId      ResourceType
---------------------------------------------------------
+ Add              AuthSSOFunction        AWS::Lambda::Function
+ Add              ChunkedTransferFunction AWS::Lambda::Function
+ Add              CleanupFunction        AWS::Lambda::Function
+ Add              DownloadS3Function     AWS::Lambda::Function
+ Add              FileFerryStateMachine  AWS::StepFunctions::StateMachine
+ Add              NotifyUserFunction     AWS::Lambda::Function
+ Add              TransferFTPFunction    AWS::Lambda::Function
+ Add              UpdateServiceNowFunction AWS::Lambda::Function
---------------------------------------------------------

Deployment time: ~3-4 minutes

Outputs:
StateMachineArn = arn:aws:states:us-east-1:637423332185:stateMachine:FileFerry-TransferStateMachine
```

## Verify Deployment:
```bash
# List all Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `FileFerry`)].FunctionName'

# Check Step Functions
aws stepfunctions list-state-machines --query 'stateMachines[?starts_with(name, `FileFerry`)].stateMachineArn'
```

## Advantages Over PowerShell:
- ⚡ **10x faster** - Parallel deployment
- 🔒 **More reliable** - Automatic rollback on failure
- 📊 **Better tracking** - CloudFormation console shows progress
- 🎯 **Idempotent** - Can re-run without issues
- ✅ **Automatic cleanup** - Removes resources if deployment fails

## Troubleshooting:

**Error: "SAM CLI not found"**
```bash
pip install aws-sam-cli --user
export PATH=$PATH:~/.local/bin
```

**Error: "Role does not exist"**
Create the Step Functions role first:
```bash
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
  --policy-arn arn:aws:iam::aws:policy/AWSLambdaRole
```

**Error: "S3 bucket not found"**
SAM creates it automatically with `--resolve-s3` flag.

## Next Steps After Deployment:
1. Copy State Machine ARN from output
2. Update `config/config.yaml` with the ARN
3. Test end-to-end transfer workflow
