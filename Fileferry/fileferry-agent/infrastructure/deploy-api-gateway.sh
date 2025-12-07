#!/bin/bash
# Deploy FileFerry API Gateway with REST API endpoints
# Run in AWS CloudShell

set -e

REGION="us-east-1"
ACCOUNT_ID="637423332185"
API_NAME="FileFerry-API"
STAGE_NAME="prod"

echo "=========================================="
echo "FileFerry API Gateway Deployment"
echo "=========================================="
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"
echo "API Name: $API_NAME"
echo "Stage: $STAGE_NAME"
echo "=========================================="

# Step 1: Deploy API Lambda functions
echo ""
echo "📦 Step 1: Deploying API Lambda functions..."
cd ~/fileferry-deployment/api_lambda_functions

for func in start_transfer get_status get_history; do
  echo "  Deploying FileFerry-API-$(echo $func | sed 's/_/-/g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1' FS=- OFS=-)..."
  zip ${func}.zip ${func}.py
  
  aws lambda create-function \
    --function-name FileFerry-API-$(echo $func | sed 's/_/-/g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1' FS=- OFS=-) \
    --runtime python3.11 \
    --role arn:aws:iam::${ACCOUNT_ID}:role/FileFerryLambdaExecutionRole \
    --handler ${func}.lambda_handler \
    --zip-file fileb://${func}.zip \
    --timeout 30 \
    --memory-size 256 \
    --environment Variables="{STATE_MACHINE_ARN=arn:aws:states:${REGION}:${ACCOUNT_ID}:stateMachine:FileFerry-TransferStateMachine,TRANSFERS_TABLE=FileFerry-TransferRequests}" \
    --region $REGION 2>/dev/null || echo "    (already exists)"
done

echo "✅ API Lambda functions deployed"

# Step 2: Create REST API
echo ""
echo "🌐 Step 2: Creating REST API..."

API_ID=$(aws apigateway create-rest-api \
  --name $API_NAME \
  --description "FileFerry File Transfer API" \
  --endpoint-configuration types=REGIONAL \
  --region $REGION \
  --query 'id' \
  --output text 2>/dev/null || \
  aws apigateway get-rest-apis --query "items[?name=='$API_NAME'].id" --output text --region $REGION)

echo "✅ API ID: $API_ID"

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query 'items[?path==`/`].id' --output text)
echo "  Root Resource ID: $ROOT_ID"

# Step 3: Create /api resource
echo ""
echo "📁 Step 3: Creating /api resource..."
API_RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part api \
  --region $REGION \
  --query 'id' \
  --output text 2>/dev/null || \
  aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api'].id" --output text)

echo "✅ /api resource created: $API_RESOURCE_ID"

# Step 4: Create /api/transfer resource
echo ""
echo "📁 Step 4: Creating /api/transfer resource..."
TRANSFER_RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $API_RESOURCE_ID \
  --path-part transfer \
  --region $REGION \
  --query 'id' \
  --output text 2>/dev/null || \
  aws apigateway get-resources --rest-api-id $API_ID --region $REGION --query "items[?path=='/api/transfer'].id" --output text)

echo "✅ /api/transfer resource created: $TRANSFER_RESOURCE_ID"

# Step 5: Create POST /api/transfer method
echo ""
echo "🔧 Step 5: Creating POST /api/transfer method..."
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $TRANSFER_RESOURCE_ID \
  --http-method POST \
  --authorization-type NONE \
  --region $REGION 2>/dev/null || echo "  (already exists)"

# Step 6: Integrate with StartTransfer Lambda
echo ""
echo "🔌 Step 6: Integrating with StartTransfer Lambda..."
START_TRANSFER_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:FileFerry-API-StartTransfer"

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $TRANSFER_RESOURCE_ID \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${START_TRANSFER_ARN}/invocations \
  --region $REGION 2>/dev/null || echo "  (already exists)"

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
  --function-name FileFerry-API-StartTransfer \
  --statement-id apigateway-invoke-start-transfer \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*" \
  --region $REGION 2>/dev/null || echo "  (permission already exists)"

echo "✅ Integration complete"

# Step 7: Deploy API
echo ""
echo "🚀 Step 7: Deploying API to $STAGE_NAME stage..."
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name $STAGE_NAME \
  --description "FileFerry API Production Deployment" \
  --region $REGION

echo "✅ API deployed"

# Step 8: Get API endpoint
echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
API_ENDPOINT="https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE_NAME}"
echo ""
echo "📋 API Endpoint:"
echo "   $API_ENDPOINT"
echo ""
echo "📝 Available Endpoints:"
echo "   POST   $API_ENDPOINT/api/transfer        - Start new transfer"
echo "   GET    $API_ENDPOINT/api/transfer/{id}   - Get transfer status"
echo "   GET    $API_ENDPOINT/api/transfers?user_id=xxx - Get transfer history"
echo ""
echo "🧪 Test with curl:"
echo 'curl -X POST '$API_ENDPOINT'/api/transfer \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"user_id":"test@example.com","source":{"type":"s3","bucket":"test"},"destination":{"type":"ftp","host":"ftp.example.com"}}'"'"
echo ""
