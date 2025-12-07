#!/bin/bash

# ============================================================================
# FileFerry API Gateway Deployment Script
# ============================================================================
# This script creates a complete REST API Gateway with 3 endpoints
# Time: ~10 minutes (automated)
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "  FileFerry API Gateway Deployment"
echo "============================================================================"
echo ""

# Configuration
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export REGION="us-east-1"
export API_NAME="FileFerry-API"
export STATE_MACHINE_ARN="arn:aws:states:${REGION}:${ACCOUNT_ID}:stateMachine:FileFerry-TransferStateMachine"

echo "✓ Account ID: ${ACCOUNT_ID}"
echo "✓ Region: ${REGION}"
echo "✓ API Name: ${API_NAME}"
echo ""

# ============================================================================
# STEP 1: Create REST API
# ============================================================================
echo "Step 1: Creating REST API..."
API_ID=$(aws apigateway create-rest-api \
    --name "${API_NAME}" \
    --description "FileFerry file transfer orchestration API" \
    --endpoint-configuration types=REGIONAL \
    --region ${REGION} \
    --query 'id' \
    --output text)

if [ -z "$API_ID" ]; then
    echo "✗ Failed to create API"
    exit 1
fi

echo "✓ API created: ${API_ID}"
echo ""

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources \
    --rest-api-id ${API_ID} \
    --region ${REGION} \
    --query 'items[0].id' \
    --output text)

echo "✓ Root resource ID: ${ROOT_ID}"
echo ""

# ============================================================================
# STEP 2: Create /transfer resource
# ============================================================================
echo "Step 2: Creating /transfer resource..."
TRANSFER_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id ${API_ID} \
    --parent-id ${ROOT_ID} \
    --path-part "transfer" \
    --region ${REGION} \
    --query 'id' \
    --output text)

echo "✓ /transfer resource created: ${TRANSFER_RESOURCE_ID}"
echo ""

# ============================================================================
# STEP 3: Create /transfer/start resource
# ============================================================================
echo "Step 3: Creating /transfer/start resource..."
START_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id ${API_ID} \
    --parent-id ${TRANSFER_RESOURCE_ID} \
    --path-part "start" \
    --region ${REGION} \
    --query 'id' \
    --output text)

echo "✓ /transfer/start resource created: ${START_RESOURCE_ID}"
echo ""

# ============================================================================
# STEP 4: Create IAM Role for API Gateway to invoke Step Functions
# ============================================================================
echo "Step 4: Creating IAM role for API Gateway..."

# Check if role exists
if aws iam get-role --role-name APIGatewayStepFunctionsRole 2>/dev/null; then
    echo "✓ IAM role already exists"
else
    # Create trust policy
    cat > /tmp/api-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "apigateway.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Create role
    aws iam create-role \
        --role-name APIGatewayStepFunctionsRole \
        --assume-role-policy-document file:///tmp/api-trust-policy.json \
        --description "Role for API Gateway to invoke Step Functions"

    # Attach policy
    cat > /tmp/api-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "states:StartExecution",
        "states:DescribeExecution",
        "states:GetExecutionHistory"
      ],
      "Resource": "${STATE_MACHINE_ARN}"
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name APIGatewayStepFunctionsRole \
        --policy-name StepFunctionsExecutionPolicy \
        --policy-document file:///tmp/api-policy.json

    echo "✓ IAM role created"
    echo "⏳ Waiting 10 seconds for IAM role propagation..."
    sleep 10
fi

ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/APIGatewayStepFunctionsRole"
echo "✓ Role ARN: ${ROLE_ARN}"
echo ""

# ============================================================================
# STEP 5: Create POST /transfer/start method
# ============================================================================
echo "Step 5: Creating POST /transfer/start method..."

# Create method
aws apigateway put-method \
    --rest-api-id ${API_ID} \
    --resource-id ${START_RESOURCE_ID} \
    --http-method POST \
    --authorization-type NONE \
    --region ${REGION} \
    --no-api-key-required

# Create integration
aws apigateway put-integration \
    --rest-api-id ${API_ID} \
    --resource-id ${START_RESOURCE_ID} \
    --http-method POST \
    --type AWS \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:states:action/StartExecution" \
    --credentials "${ROLE_ARN}" \
    --request-templates '{"application/json": "{\"stateMachineArn\": \"'"${STATE_MACHINE_ARN}"'\", \"input\": \"$util.escapeJavaScript($input.json('\'$\''))\"}"}' \
    --region ${REGION}

# Create method response
aws apigateway put-method-response \
    --rest-api-id ${API_ID} \
    --resource-id ${START_RESOURCE_ID} \
    --http-method POST \
    --status-code 200 \
    --response-models '{"application/json": "Empty"}' \
    --region ${REGION}

# Create integration response
aws apigateway put-integration-response \
    --rest-api-id ${API_ID} \
    --resource-id ${START_RESOURCE_ID} \
    --http-method POST \
    --status-code 200 \
    --response-templates '{"application/json": ""}' \
    --region ${REGION}

echo "✓ POST /transfer/start method created"
echo ""

# ============================================================================
# STEP 6: Create /transfer/status resource
# ============================================================================
echo "Step 6: Creating /transfer/status/{id} resource..."

STATUS_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id ${API_ID} \
    --parent-id ${TRANSFER_RESOURCE_ID} \
    --path-part "status" \
    --region ${REGION} \
    --query 'id' \
    --output text)

ID_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id ${API_ID} \
    --parent-id ${STATUS_RESOURCE_ID} \
    --path-part "{id}" \
    --region ${REGION} \
    --query 'id' \
    --output text)

echo "✓ /transfer/status/{id} resource created: ${ID_RESOURCE_ID}"
echo ""

# ============================================================================
# STEP 7: Create GET /transfer/status/{id} method
# ============================================================================
echo "Step 7: Creating GET /transfer/status/{id} method..."

# Get Lambda ARN
STATUS_LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:FileFerry-API-Get-Status"

# Create method
aws apigateway put-method \
    --rest-api-id ${API_ID} \
    --resource-id ${ID_RESOURCE_ID} \
    --http-method GET \
    --authorization-type NONE \
    --region ${REGION} \
    --request-parameters '{"method.request.path.id": true}' \
    --no-api-key-required

# Create integration
aws apigateway put-integration \
    --rest-api-id ${API_ID} \
    --resource-id ${ID_RESOURCE_ID} \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${STATUS_LAMBDA_ARN}/invocations" \
    --region ${REGION}

# Add Lambda permission
aws lambda add-permission \
    --function-name FileFerry-API-Get-Status \
    --statement-id apigateway-get-status-$(date +%s) \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/GET/transfer/status/*" \
    --region ${REGION} 2>/dev/null || echo "⚠ Permission already exists"

echo "✓ GET /transfer/status/{id} method created"
echo ""

# ============================================================================
# STEP 8: Create /transfer/history resource
# ============================================================================
echo "Step 8: Creating /transfer/history resource..."

HISTORY_RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id ${API_ID} \
    --parent-id ${TRANSFER_RESOURCE_ID} \
    --path-part "history" \
    --region ${REGION} \
    --query 'id' \
    --output text)

echo "✓ /transfer/history resource created: ${HISTORY_RESOURCE_ID}"
echo ""

# ============================================================================
# STEP 9: Create GET /transfer/history method
# ============================================================================
echo "Step 9: Creating GET /transfer/history method..."

# Get Lambda ARN
HISTORY_LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:FileFerry-API-Get-History"

# Create method
aws apigateway put-method \
    --rest-api-id ${API_ID} \
    --resource-id ${HISTORY_RESOURCE_ID} \
    --http-method GET \
    --authorization-type NONE \
    --region ${REGION} \
    --no-api-key-required

# Create integration
aws apigateway put-integration \
    --rest-api-id ${API_ID} \
    --resource-id ${HISTORY_RESOURCE_ID} \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${HISTORY_LAMBDA_ARN}/invocations" \
    --region ${REGION}

# Add Lambda permission
aws lambda add-permission \
    --function-name FileFerry-API-Get-History \
    --statement-id apigateway-get-history-$(date +%s) \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/GET/transfer/history" \
    --region ${REGION} 2>/dev/null || echo "⚠ Permission already exists"

echo "✓ GET /transfer/history method created"
echo ""

# ============================================================================
# STEP 10: Enable CORS on all methods
# ============================================================================
echo "Step 10: Enabling CORS..."

# Function to enable CORS on a resource
enable_cors() {
    local RESOURCE_ID=$1
    local RESOURCE_PATH=$2
    
    echo "  Enabling CORS on ${RESOURCE_PATH}..."
    
    # Create OPTIONS method
    aws apigateway put-method \
        --rest-api-id ${API_ID} \
        --resource-id ${RESOURCE_ID} \
        --http-method OPTIONS \
        --authorization-type NONE \
        --region ${REGION} 2>/dev/null || true
    
    # Create OPTIONS integration
    aws apigateway put-integration \
        --rest-api-id ${API_ID} \
        --resource-id ${RESOURCE_ID} \
        --http-method OPTIONS \
        --type MOCK \
        --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
        --region ${REGION} 2>/dev/null || true
    
    # Create OPTIONS method response
    aws apigateway put-method-response \
        --rest-api-id ${API_ID} \
        --resource-id ${RESOURCE_ID} \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers": true, "method.response.header.Access-Control-Allow-Methods": true, "method.response.header.Access-Control-Allow-Origin": true}' \
        --region ${REGION} 2>/dev/null || true
    
    # Create OPTIONS integration response
    aws apigateway put-integration-response \
        --rest-api-id ${API_ID} \
        --resource-id ${RESOURCE_ID} \
        --http-method OPTIONS \
        --status-code 200 \
        --response-parameters '{"method.response.header.Access-Control-Allow-Headers": "'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'", "method.response.header.Access-Control-Allow-Methods": "'"'"'GET,POST,OPTIONS'"'"'", "method.response.header.Access-Control-Allow-Origin": "'"'"'*'"'"'"}' \
        --region ${REGION} 2>/dev/null || true
}

# Enable CORS on all resources
enable_cors ${START_RESOURCE_ID} "/transfer/start"
enable_cors ${ID_RESOURCE_ID} "/transfer/status/{id}"
enable_cors ${HISTORY_RESOURCE_ID} "/transfer/history"

echo "✓ CORS enabled on all endpoints"
echo ""

# ============================================================================
# STEP 11: Deploy API to prod stage
# ============================================================================
echo "Step 11: Deploying API to prod stage..."

aws apigateway create-deployment \
    --rest-api-id ${API_ID} \
    --stage-name prod \
    --stage-description "Production stage for FileFerry API" \
    --description "Initial deployment" \
    --region ${REGION}

echo "✓ API deployed to prod stage"
echo ""

# ============================================================================
# DEPLOYMENT COMPLETE
# ============================================================================
echo "============================================================================"
echo "  ✅ API Gateway Deployment Complete!"
echo "============================================================================"
echo ""
echo "📋 API Details:"
echo "  • API ID: ${API_ID}"
echo "  • API Name: ${API_NAME}"
echo "  • Region: ${REGION}"
echo "  • Stage: prod"
echo ""
echo "🌐 API Endpoint URLs:"
echo "  • Base URL: https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod"
echo ""
echo "  • POST /transfer/start"
echo "    https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/transfer/start"
echo ""
echo "  • GET /transfer/status/{id}"
echo "    https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/transfer/status/{id}"
echo ""
echo "  • GET /transfer/history"
echo "    https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/transfer/history"
echo ""
echo "============================================================================"
echo "📝 Next Steps:"
echo "============================================================================"
echo ""
echo "1. Test the API:"
echo "   curl -X POST https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/transfer/start \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d @test_input.json"
echo ""
echo "2. Update frontend with API URL:"
echo "   const API_BASE_URL = 'https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod';"
echo ""
echo "3. View API in AWS Console:"
echo "   https://${REGION}.console.aws.amazon.com/apigateway/main/apis/${API_ID}?region=${REGION}"
echo ""
echo "============================================================================"
echo "🎉 FileFerry is now 100% deployed!"
echo "============================================================================"

# Save API ID to file for later use
echo "${API_ID}" > /tmp/fileferry-api-id.txt
echo ""
echo "✓ API ID saved to: /tmp/fileferry-api-id.txt"
