#!/bin/bash
# ============================================================
# FileFerry Lambda Deployment - AWS CloudShell
# ============================================================
# Copy this entire file and paste into AWS CloudShell

echo "════════════════════════════════════════════════════════"
echo "FileFerry Lambda Functions Deployment"
echo "════════════════════════════════════════════════════════"
echo ""

# Step 1: Set environment variables (AUTO-DETECT ACCOUNT ID)
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export REGION="us-east-1"

echo "✅ Account ID: $ACCOUNT_ID"
echo "✅ Region: $REGION"
echo ""

# Step 2: Create IAM role (if doesn't exist)
echo "📋 Creating IAM role..."
aws iam create-role \
    --role-name FileFerryLambdaExecutionRole \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }]
    }' 2>/dev/null || echo "✅ Role already exists"

# Step 3: Attach policies
echo "📋 Attaching IAM policies..."
aws iam attach-role-policy \
    --role-name FileFerryLambdaExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
    --role-name FileFerryLambdaExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

aws iam attach-role-policy \
    --role-name FileFerryLambdaExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

echo "⏳ Waiting 10 seconds for IAM role to propagate..."
sleep 10
echo ""

# Step 4: Deploy Lambda functions
echo "════════════════════════════════════════════════════════"
echo "📦 Deploying 7 Lambda Functions..."
echo "════════════════════════════════════════════════════════"
echo ""

# Lambda 1: AuthSSO
echo "1/7 Deploying FileFerry-AuthSSO..."
zip -q auth_sso.zip auth_sso.py
aws lambda create-function \
    --function-name FileFerry-AuthSSO \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler auth_sso.lambda_handler \
    --zip-file fileb://auth_sso.zip \
    --timeout 30 \
    --memory-size 512 \
    --environment 'Variables={DYNAMODB_TABLE=FileFerry-ActiveSessions}' \
    --region $REGION > /dev/null 2>&1 && echo "   ✅ FileFerry-AuthSSO deployed" || echo "   ⚠️  Already exists or error"

# Lambda 2: DownloadS3
echo "2/7 Deploying FileFerry-DownloadS3..."
zip -q download_s3.zip download_s3.py
aws lambda create-function \
    --function-name FileFerry-DownloadS3 \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler download_s3.lambda_handler \
    --zip-file fileb://download_s3.zip \
    --timeout 300 \
    --memory-size 1024 \
    --environment 'Variables={DYNAMODB_CACHE_TABLE=FileFerry-S3FileCache,CACHE_TTL=86400}' \
    --region $REGION > /dev/null 2>&1 && echo "   ✅ FileFerry-DownloadS3 deployed" || echo "   ⚠️  Already exists or error"

# Lambda 3: TransferFTP
echo "3/7 Deploying FileFerry-TransferFTP..."
zip -q transfer_ftp.zip transfer_ftp.py
aws lambda create-function \
    --function-name FileFerry-TransferFTP \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler transfer_ftp.lambda_handler \
    --zip-file fileb://transfer_ftp.zip \
    --timeout 900 \
    --memory-size 1024 \
    --environment 'Variables={CHUNK_SIZE=10485760,MAX_RETRIES=3}' \
    --region $REGION > /dev/null 2>&1 && echo "   ✅ FileFerry-TransferFTP deployed" || echo "   ⚠️  Already exists or error"

# Lambda 4: ChunkedTransfer
echo "4/7 Deploying FileFerry-ChunkedTransfer..."
zip -q chunked_transfer.zip chunked_transfer.py
aws lambda create-function \
    --function-name FileFerry-ChunkedTransfer \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler chunked_transfer.lambda_handler \
    --zip-file fileb://chunked_transfer.zip \
    --timeout 900 \
    --memory-size 2048 \
    --environment 'Variables={CHUNK_SIZE=104857600,PARALLEL_CHUNKS=4}' \
    --region $REGION > /dev/null 2>&1 && echo "   ✅ FileFerry-ChunkedTransfer deployed" || echo "   ⚠️  Already exists or error"

# Lambda 5: UpdateServiceNow
echo "5/7 Deploying FileFerry-UpdateServiceNow..."
zip -q update_servicenow.zip update_servicenow.py
aws lambda create-function \
    --function-name FileFerry-UpdateServiceNow \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler update_servicenow.lambda_handler \
    --zip-file fileb://update_servicenow.zip \
    --timeout 60 \
    --memory-size 512 \
    --environment 'Variables={SERVICENOW_INSTANCE_URL=https://dev329630.service-now.com}' \
    --region $REGION > /dev/null 2>&1 && echo "   ✅ FileFerry-UpdateServiceNow deployed" || echo "   ⚠️  Already exists or error"

# Lambda 6: NotifyUser
echo "6/7 Deploying FileFerry-NotifyUser..."
zip -q notify_user.zip notify_user.py
aws lambda create-function \
    --function-name FileFerry-NotifyUser \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler notify_user.lambda_handler \
    --zip-file fileb://notify_user.zip \
    --timeout 30 \
    --memory-size 512 \
    --environment 'Variables={DYNAMODB_TABLE=FileFerry-TransferRequests}' \
    --region $REGION > /dev/null 2>&1 && echo "   ✅ FileFerry-NotifyUser deployed" || echo "   ⚠️  Already exists or error"

# Lambda 7: Cleanup
echo "7/7 Deploying FileFerry-Cleanup..."
zip -q cleanup.zip cleanup.py
aws lambda create-function \
    --function-name FileFerry-Cleanup \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler cleanup.lambda_handler \
    --zip-file fileb://cleanup.zip \
    --timeout 60 \
    --memory-size 256 \
    --environment 'Variables={DYNAMODB_SESSION_TABLE=FileFerry-ActiveSessions}' \
    --region $REGION > /dev/null 2>&1 && echo "   ✅ FileFerry-Cleanup deployed" || echo "   ⚠️  Already exists or error"

# Step 5: Verify deployment
echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE! Listing all Lambda functions:"
echo "════════════════════════════════════════════════════════"
aws lambda list-functions \
    --query 'Functions[?starts_with(FunctionName, `FileFerry`)].FunctionName' \
    --output table \
    --region $REGION

echo ""
echo "✅ You should see 8 Lambda functions listed above"
echo ""
echo "Next steps:"
echo "  1. Test FileFerry-AuthSSO function"
echo "  2. Create Step Functions State Machine"
echo "  3. Create API Gateway"
echo ""
