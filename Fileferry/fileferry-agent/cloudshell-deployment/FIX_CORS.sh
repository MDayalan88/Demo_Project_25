#!/bin/bash

# Fix CORS for API Gateway POST /transfer/start endpoint
# This script updates the CORS headers to allow browser access

set -e

API_ID="gwosr3m399"
REGION="us-east-1"

echo "🔧 Fixing CORS for API Gateway..."
echo "API ID: $API_ID"
echo ""

# Get the resource ID for /transfer/start
echo "📋 Getting resource IDs..."
START_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region $REGION \
    --query 'items[?path==`/transfer/start`].id' \
    --output text)

echo "✅ /transfer/start resource ID: $START_RESOURCE_ID"

# Delete existing integration response first
echo ""
echo "🗑️ Removing existing integration response..."
aws apigateway delete-integration-response \
    --rest-api-id $API_ID \
    --resource-id $START_RESOURCE_ID \
    --http-method POST \
    --status-code 200 \
    --region $REGION 2>/dev/null || echo "No existing integration response to delete"

# Delete existing method response
echo ""
echo "🗑️ Removing existing method response..."
aws apigateway delete-method-response \
    --rest-api-id $API_ID \
    --resource-id $START_RESOURCE_ID \
    --http-method POST \
    --status-code 200 \
    --region $REGION 2>/dev/null || echo "No existing method response to delete"

# Create method response with CORS headers
echo ""
echo "🔧 Creating method response with CORS headers..."
aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $START_RESOURCE_ID \
    --http-method POST \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Origin": true
    }' \
    --region $REGION

# Create integration response with CORS headers
echo ""
echo "🔧 Creating integration response with CORS headers..."
aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $START_RESOURCE_ID \
    --http-method POST \
    --status-code 200 \
    --response-parameters '{
        "method.response.header.Access-Control-Allow-Origin": "'"'"'*'"'"'"
    }' \
    --region $REGION

echo ""
echo "🚀 Deploying changes to prod stage..."
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --description "Fix CORS headers for POST /transfer/start" \
    --region $REGION

echo ""
echo "✅ CORS Fix Applied!"
echo ""
echo "Wait 10 seconds, then try demo.html again!"
echo "The transfer should now work without CORS errors."
echo ""
