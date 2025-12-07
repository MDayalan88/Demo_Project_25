#!/bin/bash

echo "=================================="
echo "FileFerry API Gateway Status Check"
echo "=================================="
echo ""

REGION="us-east-1"

echo "1. Checking API Lambda Functions..."
echo "-----------------------------------"
aws lambda list-functions --region $REGION \
  --query 'Functions[?starts_with(FunctionName, `FileFerry-API`)].{Name:FunctionName,Runtime:Runtime,Modified:LastModified}' \
  --output table

echo ""
echo "2. Checking REST APIs..."
echo "------------------------"
aws apigateway get-rest-apis --region $REGION \
  --query 'items[?name==`FileFerry-API`].{Name:name,ID:id,Created:createdDate}' \
  --output table

echo ""
echo "3. Getting API Endpoint (if deployed)..."
echo "-----------------------------------------"
API_ID=$(aws apigateway get-rest-apis --region $REGION \
  --query 'items[?name==`FileFerry-API`].id' \
  --output text)

if [ -n "$API_ID" ]; then
  echo "API ID: $API_ID"
  echo "Endpoint: https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod"
  
  echo ""
  echo "4. Checking API Resources..."
  echo "----------------------------"
  aws apigateway get-resources --rest-api-id $API_ID --region $REGION \
    --query 'items[].{Path:path,ID:id}' \
    --output table
else
  echo "No FileFerry-API found yet."
fi

echo ""
echo "5. Checking Phase 3 Lambda Functions..."
echo "----------------------------------------"
aws lambda list-functions --region $REGION \
  --query 'Functions[?starts_with(FunctionName, `FileFerry-`)].{Name:FunctionName,Modified:LastModified}' \
  --output table

echo ""
echo "6. Checking Step Functions State Machine..."
echo "--------------------------------------------"
aws stepfunctions list-state-machines --region $REGION \
  --query 'stateMachines[?name==`FileFerry-TransferStateMachine`].{Name:name,Status:status,ARN:stateMachineArn}' \
  --output table

echo ""
echo "=================================="
echo "Status Check Complete"
echo "=================================="
