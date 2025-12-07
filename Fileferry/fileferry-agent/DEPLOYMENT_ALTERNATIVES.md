# 🚀 AWS Deployment Guide - Alternative Options

**Issue**: Cannot install AWS CLI on work laptop (admin rights required)

---

## ✅ What's Ready to Deploy

- ✅ 8 Lambda functions (validate, auth, download, transfer, chunked, servicenow, notify, cleanup)
- ✅ Step Functions state machine JSON
- ✅ Deployment automation script (`infrastructure/deploy-phase3.ps1`)
- ✅ IAM policies and roles defined
- ✅ ServiceNow integration tested and working

**All code is written and ready - just needs AWS deployment!**

---

## 🔧 Alternative Deployment Options

### Option 1: AWS CloudShell (Recommended - No Install Needed!) ⭐

**CloudShell** is a browser-based terminal with AWS CLI pre-installed.

**Steps**:
1. **Login to AWS Console**:
   - Go to: https://console.aws.amazon.com
   - Login with account: 637423332185

2. **Open CloudShell**:
   - Click the CloudShell icon (>_) in top-right corner
   - Or search for "CloudShell" in AWS Console

3. **Upload project files**:
   ```bash
   # In CloudShell, upload the infrastructure folder
   # Click Actions > Upload file
   # Upload: infrastructure/deploy-phase3.ps1 and lambda_functions folder
   ```

4. **Install PowerShell in CloudShell** (if needed):
   ```bash
   # CloudShell uses Linux - convert to bash or use pwsh
   sudo yum install -y powershell
   ```

5. **Run deployment**:
   ```bash
   pwsh infrastructure/deploy-phase3.ps1 -Region us-east-1 -AccountId 637423332185
   ```

---

### Option 2: AWS Cloud9 IDE (Browser-Based Development)

**Cloud9** is a full IDE in your browser with AWS CLI pre-configured.

**Steps**:
1. **Open Cloud9**:
   - Go to: https://console.aws.amazon.com/cloud9
   - Click "Create environment"
   - Name: "FileFerry-Deployment"
   - Environment type: New EC2 instance (t2.micro - free tier)

2. **Clone your GitHub repo**:
   ```bash
   git clone https://github.com/MDayalan88/Demo_Project_25.git
   cd Demo_Project_25/fileferry-agent
   ```

3. **Run deployment**:
   ```bash
   cd infrastructure
   pwsh deploy-phase3.ps1 -Region us-east-1 -AccountId 637423332185
   ```

4. **Delete environment** after deployment to save costs

---

### Option 3: GitHub Actions CI/CD (Fully Automated)

Set up automated deployment via GitHub Actions.

**Steps**:
1. **Add AWS credentials to GitHub Secrets**:
   - Go to: https://github.com/MDayalan88/Demo_Project_25/settings/secrets/actions
   - Add secrets:
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`
     - `AWS_REGION`: us-east-1
     - `AWS_ACCOUNT_ID`: 637423332185

2. **Create GitHub Actions workflow**:

Create file: `.github/workflows/deploy-phase3.yml`

```yaml
name: Deploy FileFerry Phase 3

on:
  workflow_dispatch:  # Manual trigger
  push:
    branches: [master]
    paths:
      - 'fileferry-agent/infrastructure/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Install PowerShell
        run: |
          sudo apt-get update
          sudo apt-get install -y powershell

      - name: Deploy Phase 3
        run: |
          cd fileferry-agent/infrastructure
          pwsh deploy-phase3.ps1 -Region ${{ secrets.AWS_REGION }} -AccountId ${{ secrets.AWS_ACCOUNT_ID }}

      - name: Upload deployment logs
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: deployment-logs
          path: fileferry-agent/infrastructure/deploy-*.log
```

3. **Trigger deployment**:
   - Go to: https://github.com/MDayalan88/Demo_Project_25/actions
   - Click "Deploy FileFerry Phase 3"
   - Click "Run workflow"

---

### Option 4: Personal Computer with AWS CLI

If you have a personal laptop or home computer:

**Steps**:
1. **Install AWS CLI**:
   - Download: https://awscli.amazonaws.com/AWSCLIV2.msi
   - Or use winget: `winget install Amazon.AWSCLI`

2. **Configure AWS credentials**:
   ```powershell
   aws configure
   # Enter: Access Key ID, Secret Access Key, us-east-1, json
   ```

3. **Clone GitHub repo**:
   ```powershell
   git clone https://github.com/MDayalan88/Demo_Project_25.git
   cd Demo_Project_25/fileferry-agent
   ```

4. **Run deployment**:
   ```powershell
   cd infrastructure
   .\deploy-phase3.ps1 -Region us-east-1 -AccountId 637423332185
   ```

---

### Option 5: AWS Systems Manager Session Manager

Use SSM to access EC2 instance without SSH keys.

**Steps**:
1. **Launch temporary EC2 instance**:
   - Go to EC2 Console
   - Launch t2.micro (free tier)
   - Attach IAM role with: AmazonSSMManagedInstanceCore

2. **Connect via Session Manager**:
   - Select instance → Connect → Session Manager
   - Opens browser-based terminal

3. **Install tools and deploy**:
   ```bash
   sudo yum install -y git aws-cli powershell
   git clone https://github.com/MDayalan88/Demo_Project_25.git
   cd Demo_Project_25/fileferry-agent/infrastructure
   pwsh deploy-phase3.ps1 -Region us-east-1 -AccountId 637423332185
   ```

4. **Terminate instance** after deployment

---

## 📋 What Will Be Deployed

When you run the deployment script, it will create:

### IAM Roles (2)
- **FileFerryLambdaExecutionRole**:
  - S3 read/write access
  - DynamoDB read/write access
  - CloudWatch Logs
  - X-Ray tracing
  - Step Functions invocation

- **FileFerryStepFunctionsRole**:
  - Lambda function invocation
  - CloudWatch Logs
  - State machine execution

### Lambda Functions (8)
1. **FileFerry-ValidateInput** (128 MB, 30s timeout)
2. **FileFerry-AuthSSO** (128 MB, 30s timeout)
3. **FileFerry-DownloadS3** (512 MB, 60s timeout)
4. **FileFerry-TransferFTP** (512 MB, 300s timeout)
5. **FileFerry-ChunkedTransfer** (1024 MB, 300s timeout)
6. **FileFerry-UpdateServiceNow** (256 MB, 60s timeout)
7. **FileFerry-NotifyUser** (256 MB, 30s timeout)
8. **FileFerry-Cleanup** (128 MB, 30s timeout)

### Step Functions State Machine
- **Name**: FileFerry-TransferStateMachine
- **Type**: Standard workflow
- **States**: 8 (ValidateInput → AuthSSO → DownloadS3 → TransferFTP → ChunkedTransfer → UpdateServiceNow → NotifyUser → Cleanup)

---

## 💰 Estimated Costs

### Monthly Cost (100 transfers/month)
- Lambda executions: ~$0.50
- Step Functions: ~$0.025
- DynamoDB: $0 (free tier - 25GB storage)
- S3: $0.023/GB stored
- **Total**: ~$5-10/month

### Per Transfer Cost
- ~$0.001-0.01 per transfer (depending on file size)

---

## ⏱️ Deployment Timeline

| Step | Duration |
|------|----------|
| Create IAM roles | 2-3 minutes |
| Package Lambda functions | 5-10 minutes |
| Deploy 8 Lambda functions | 10-15 minutes |
| Create Step Functions | 2-3 minutes |
| Verify deployment | 5 minutes |
| **Total** | **30-45 minutes** |

---

## ✅ Post-Deployment Steps

After deployment completes:

1. **Update config.yaml**:
   ```yaml
   step_functions:
     state_machine_arn: "arn:aws:states:us-east-1:637423332185:stateMachine:FileFerry-TransferStateMachine"
   ```

2. **Test Lambda functions individually**:
   - Go to Lambda Console
   - Select FileFerry-ValidateInput
   - Create test event with sample JSON
   - Invoke and check logs

3. **Test Step Functions execution**:
   - Go to Step Functions Console
   - Select FileFerry-TransferStateMachine
   - Start execution with test input
   - Monitor execution progress

4. **Monitor CloudWatch Logs**:
   - Go to CloudWatch Console
   - Check log groups: `/aws/lambda/FileFerry-*`
   - Review execution logs

---

## 🎯 Recommended Approach

**Best Option**: **AWS CloudShell** (Option 1) ⭐

**Why?**:
- ✅ No software installation required
- ✅ AWS CLI pre-configured
- ✅ Already authenticated
- ✅ Free to use
- ✅ Works from any browser
- ✅ No cleanup needed

**Steps**:
1. Login to AWS Console
2. Click CloudShell icon
3. Upload infrastructure files
4. Run deployment script
5. Done!

---

## 📞 Need Help?

If you encounter issues:

1. Check CloudWatch Logs for Lambda errors
2. Review IAM role permissions
3. Verify DynamoDB tables exist
4. Check Step Functions execution history
5. Review deployment script output logs

---

## 🚀 Ready to Deploy!

**Your FileFerry code is 100% ready for AWS deployment.**

Choose your preferred deployment method above and follow the steps.

The deployment script handles everything automatically:
- ✅ Creates all resources
- ✅ Sets up permissions
- ✅ Configures integrations
- ✅ Validates deployment

**Good luck with the deployment!** 🎉

---

**Last Updated**: December 3, 2025  
**Status**: Ready for AWS deployment via CloudShell, Cloud9, GitHub Actions, or personal computer
