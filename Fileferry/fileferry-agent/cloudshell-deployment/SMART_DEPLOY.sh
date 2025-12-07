#!/bin/bash
# ============================================================
# FileFerry Lambda Deployment - SMART DEPLOY
# Checks if function exists and updates instead of creating
# ============================================================

echo "════════════════════════════════════════════════════════"
echo "FileFerry Lambda Functions - Smart Deployment"
echo "════════════════════════════════════════════════════════"
echo ""

# Step 1: Set environment variables
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export REGION="us-east-1"

echo "✅ Account ID: $ACCOUNT_ID"
echo "✅ Region: $REGION"
echo ""

# Step 2: Check current deployment status
echo "📊 Checking existing Lambda functions..."
aws lambda list-functions \
    --query 'Functions[?starts_with(FunctionName, `FileFerry`)].FunctionName' \
    --output text \
    --region $REGION

echo ""
echo "════════════════════════════════════════════════════════"
echo "📦 Deploying/Updating Lambda Functions..."
echo "════════════════════════════════════════════════════════"
echo ""

# Function to deploy or update Lambda
deploy_lambda() {
    local func_name=$1
    local file_name=$2
    local handler=$3
    local timeout=$4
    local memory=$5
    local env_vars=$6
    
    echo "Processing $func_name..."
    
    # Create ZIP
    zip -q ${file_name}.zip ${file_name}.py
    
    # Check if function exists
    if aws lambda get-function --function-name $func_name --region $REGION > /dev/null 2>&1; then
        # Update existing function
        echo "  ⚠️  Function exists, updating code..."
        aws lambda update-function-code \
            --function-name $func_name \
            --zip-file fileb://${file_name}.zip \
            --region $REGION > /dev/null 2>&1
        
        # Update configuration
        aws lambda update-function-configuration \
            --function-name $func_name \
            --timeout $timeout \
            --memory-size $memory \
            --environment "$env_vars" \
            --region $REGION > /dev/null 2>&1
        
        echo "  ✅ $func_name updated successfully"
    else
        # Create new function
        echo "  📦 Creating new function..."
        aws lambda create-function \
            --function-name $func_name \
            --runtime python3.11 \
            --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
            --handler $handler \
            --zip-file fileb://${file_name}.zip \
            --timeout $timeout \
            --memory-size $memory \
            --environment "$env_vars" \
            --region $REGION > /dev/null 2>&1
        
        echo "  ✅ $func_name created successfully"
    fi
    
    # Clean up ZIP
    rm -f ${file_name}.zip
}

# Deploy all 7 functions
deploy_lambda "FileFerry-AuthSSO" "auth_sso" "auth_sso.lambda_handler" 30 512 \
    "Variables={DYNAMODB_TABLE=FileFerry-ActiveSessions}"

deploy_lambda "FileFerry-DownloadS3" "download_s3" "download_s3.lambda_handler" 300 1024 \
    "Variables={DYNAMODB_CACHE_TABLE=FileFerry-S3FileCache,CACHE_TTL=86400}"

deploy_lambda "FileFerry-TransferFTP" "transfer_ftp" "transfer_ftp.lambda_handler" 900 1024 \
    "Variables={CHUNK_SIZE=10485760,MAX_RETRIES=3}"

deploy_lambda "FileFerry-ChunkedTransfer" "chunked_transfer" "chunked_transfer.lambda_handler" 900 2048 \
    "Variables={CHUNK_SIZE=104857600,PARALLEL_CHUNKS=4}"

deploy_lambda "FileFerry-UpdateServiceNow" "update_servicenow" "update_servicenow.lambda_handler" 60 512 \
    "Variables={SERVICENOW_INSTANCE_URL=https://dev329630.service-now.com}"

deploy_lambda "FileFerry-NotifyUser" "notify_user" "notify_user.lambda_handler" 30 512 \
    "Variables={DYNAMODB_TABLE=FileFerry-TransferRequests}"

deploy_lambda "FileFerry-Cleanup" "cleanup" "cleanup.lambda_handler" 60 256 \
    "Variables={DYNAMODB_SESSION_TABLE=FileFerry-ActiveSessions}"

# Final verification
echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📊 All FileFerry Lambda Functions:"
aws lambda list-functions \
    --query 'Functions[?starts_with(FunctionName, `FileFerry`)].{Name:FunctionName,Runtime:Runtime,Memory:MemorySize,Timeout:Timeout}' \
    --output table \
    --region $REGION

echo ""
echo "🎯 Function Count:"
FUNC_COUNT=$(aws lambda list-functions \
    --query 'length(Functions[?starts_with(FunctionName, `FileFerry`)])' \
    --output text \
    --region $REGION)
echo "   Total: $FUNC_COUNT/8 functions deployed"
echo ""

if [ "$FUNC_COUNT" -eq 8 ]; then
    echo "✅ SUCCESS! All 8 Lambda functions are deployed!"
    echo ""
    echo "Next steps:"
    echo "  1. Test a function: aws lambda invoke --function-name FileFerry-AuthSSO --payload '{\"user_id\":\"test\",\"servicenow_tickets\":[\"INC001\"]}' response.json"
    echo "  2. Create Step Functions State Machine"
    echo "  3. Create API Gateway"
else
    echo "⚠️  Only $FUNC_COUNT/8 functions deployed"
    echo "   Missing: FileFerry-ValidateInput (should be deployed separately)"
fi
echo ""
