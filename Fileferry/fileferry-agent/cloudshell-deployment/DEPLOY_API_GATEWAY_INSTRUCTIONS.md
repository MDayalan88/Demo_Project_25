# 🚀 API Gateway Deployment Instructions

## ✅ Pre-Deployment Checklist

**Current Status:**
- ✅ 14 Lambda functions deployed
- ✅ 5 DynamoDB tables ACTIVE
- ✅ Step Functions State Machine ACTIVE
- ✅ IAM roles configured
- ⏳ API Gateway (deploying now)

---

## 📋 Step-by-Step Deployment Guide

### **Step 1: Open AWS CloudShell** (2 minutes)

1. Go to: https://console.aws.amazon.com
2. Login with your AWS account (637423332185)
3. Ensure you're in **us-east-1** region (top-right dropdown)
4. Click **CloudShell** icon (bottom-left toolbar) or search "CloudShell"
5. Wait for CloudShell terminal to load (~30 seconds)

---

### **Step 2: Upload Deployment Script** (3 minutes)

**Option A: Copy-Paste Method (Recommended)**

```bash
# Create the deployment script
cat > deploy-api-gateway.sh << 'EOF'
#!/bin/bash

# ============================================================================
# FileFerry API Gateway Deployment Script
# ============================================================================

set -e  # Exit on error

echo "🚀 Starting FileFerry API Gateway Deployment..."
echo "Region: us-east-1"
echo "Account: $(aws sts get-caller-identity --query Account --output text)"
echo ""

# Get Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
STATE_MACHINE_ARN="arn:aws:states:us-east-1:${ACCOUNT_ID}:stateMachine:FileFerryTransferStateMachine"

echo "📍 State Machine ARN: $STATE_MACHINE_ARN"
echo ""

# ============================================================================
# Step 1: Create REST API
# ============================================================================
echo "🔧 [1/11] Creating REST API..."

API_ID=$(aws apigateway create-rest-api \
  --name "FileFerry-API" \
  --description "API Gateway for FileFerry file transfer system" \
  --endpoint-configuration types=REGIONAL \
  --query 'id' \
  --output text)

echo "✅ API Created: $API_ID"

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[?path==`/`].id' \
  --output text)

echo "✅ Root Resource ID: $ROOT_ID"
echo ""

# ============================================================================
# Step 2: Create /transfer resource
# ============================================================================
echo "🔧 [2/11] Creating /transfer resource..."

TRANSFER_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part "transfer" \
  --query 'id' \
  --output text)

echo "✅ /transfer created: $TRANSFER_ID"
echo ""

# ============================================================================
# Step 3: Create /transfer/start resource
# ============================================================================
echo "🔧 [3/11] Creating /transfer/start resource..."

START_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $TRANSFER_ID \
  --path-part "start" \
  --query 'id' \
  --output text)

echo "✅ /transfer/start created: $START_ID"
echo ""

# ============================================================================
# Step 4: Create IAM Role for API Gateway
# ============================================================================
echo "🔧 [4/11] Creating IAM role for API Gateway..."

# Create trust policy
cat > /tmp/api-trust-policy.json << 'TRUST_EOF'
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
TRUST_EOF

# Create role
aws iam create-role \
  --role-name APIGatewayStepFunctionsRole \
  --assume-role-policy-document file:///tmp/api-trust-policy.json \
  --description "Role for API Gateway to invoke Step Functions" \
  2>/dev/null || echo "Role already exists"

# Attach policy
cat > /tmp/api-policy.json << POLICY_EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "states:StartExecution"
      ],
      "Resource": [
        "${STATE_MACHINE_ARN}"
      ]
    }
  ]
}
POLICY_EOF

aws iam put-role-policy \
  --role-name APIGatewayStepFunctionsRole \
  --policy-name StepFunctionsExecutionPolicy \
  --policy-document file:///tmp/api-policy.json

echo "✅ IAM Role created: APIGatewayStepFunctionsRole"
echo ""

# Wait for IAM role to propagate
echo "⏳ Waiting 10 seconds for IAM role to propagate..."
sleep 10

# ============================================================================
# Step 5: Create POST method for /transfer/start
# ============================================================================
echo "🔧 [5/11] Creating POST /transfer/start method..."

# Create method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $START_ID \
  --http-method POST \
  --authorization-type NONE \
  --request-parameters "method.request.header.Content-Type=true"

echo "✅ POST method created"

# Create integration
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/APIGatewayStepFunctionsRole"

aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $START_ID \
  --http-method POST \
  --type AWS \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:us-east-1:states:action/StartExecution" \
  --credentials "$ROLE_ARN" \
  --request-templates '{
    "application/json": "{\"input\": \"$util.escapeJavaScript($input.json('"'"'$'"'"'))\", \"stateMachineArn\": \"'"$STATE_MACHINE_ARN"'\"}"
  }'

echo "✅ Step Functions integration configured"

# Create method response
aws apigateway put-method-response \
  --rest-api-id $API_ID \
  --resource-id $START_ID \
  --http-method POST \
  --status-code 200 \
  --response-models '{"application/json": "Empty"}' \
  --response-parameters '{
    "method.response.header.Access-Control-Allow-Origin": false,
    "method.response.header.Access-Control-Allow-Headers": false,
    "method.response.header.Access-Control-Allow-Methods": false
  }'

# Create integration response
aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id $START_ID \
  --http-method POST \
  --status-code 200 \
  --response-templates '{"application/json": ""}' \
  --response-parameters '{
    "method.response.header.Access-Control-Allow-Origin": "'"'"'*'"'"'",
    "method.response.header.Access-Control-Allow-Headers": "'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'",
    "method.response.header.Access-Control-Allow-Methods": "'"'"'POST,OPTIONS'"'"'"
  }'

echo "✅ /transfer/start endpoint configured"
echo ""

# ============================================================================
# Step 6: Create /transfer/status resource
# ============================================================================
echo "🔧 [6/11] Creating /transfer/status/{id} resource..."

STATUS_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $TRANSFER_ID \
  --path-part "status" \
  --query 'id' \
  --output text)

STATUS_DETAIL_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $STATUS_ID \
  --path-part "{id}" \
  --query 'id' \
  --output text)

echo "✅ /transfer/status/{id} created: $STATUS_DETAIL_ID"
echo ""

# ============================================================================
# Step 7: Create GET method for /transfer/status/{id}
# ============================================================================
echo "🔧 [7/11] Creating GET /transfer/status/{id} method..."

# Get GetTransferStatus Lambda ARN
LAMBDA_ARN="arn:aws:lambda:us-east-1:${ACCOUNT_ID}:function:FileFerry-GetTransferStatus"

# Create method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $STATUS_DETAIL_ID \
  --http-method GET \
  --authorization-type NONE \
  --request-parameters "method.request.path.id=true"

# Create integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $STATUS_DETAIL_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations"

# Add Lambda permission
aws lambda add-permission \
  --function-name FileFerry-GetTransferStatus \
  --statement-id apigateway-get-status \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*/*" \
  2>/dev/null || echo "Permission already exists"

echo "✅ GET /transfer/status/{id} configured"
echo ""

# ============================================================================
# Step 8: Create /transfer/history resource
# ============================================================================
echo "🔧 [8/11] Creating /transfer/history resource..."

HISTORY_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $TRANSFER_ID \
  --path-part "history" \
  --query 'id' \
  --output text)

echo "✅ /transfer/history created: $HISTORY_ID"
echo ""

# ============================================================================
# Step 9: Create GET method for /transfer/history
# ============================================================================
echo "🔧 [9/11] Creating GET /transfer/history method..."

# Get GetTransferHistory Lambda ARN
LAMBDA_HISTORY_ARN="arn:aws:lambda:us-east-1:${ACCOUNT_ID}:function:FileFerry-GetTransferHistory"

# Create method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $HISTORY_ID \
  --http-method GET \
  --authorization-type NONE

# Create integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $HISTORY_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/${LAMBDA_HISTORY_ARN}/invocations"

# Add Lambda permission
aws lambda add-permission \
  --function-name FileFerry-GetTransferHistory \
  --statement-id apigateway-get-history \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*/*" \
  2>/dev/null || echo "Permission already exists"

echo "✅ GET /transfer/history configured"
echo ""

# ============================================================================
# Step 10: Enable CORS on all endpoints
# ============================================================================
echo "🔧 [10/11] Enabling CORS on all endpoints..."

# Function to enable CORS
enable_cors() {
  local RESOURCE_ID=$1
  local RESOURCE_NAME=$2
  
  echo "   Enabling CORS for $RESOURCE_NAME..."
  
  # Create OPTIONS method
  aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --authorization-type NONE \
    2>/dev/null || true
  
  # Create MOCK integration
  aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json": "{\"statusCode\": 200}"}' \
    2>/dev/null || true
  
  # Create method response
  aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{
      "method.response.header.Access-Control-Allow-Origin": false,
      "method.response.header.Access-Control-Allow-Headers": false,
      "method.response.header.Access-Control-Allow-Methods": false
    }' \
    --response-models '{"application/json": "Empty"}' \
    2>/dev/null || true
  
  # Create integration response
  aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{
      "method.response.header.Access-Control-Allow-Origin": "'"'"'*'"'"'",
      "method.response.header.Access-Control-Allow-Headers": "'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'",
      "method.response.header.Access-Control-Allow-Methods": "'"'"'GET,POST,OPTIONS'"'"'"
    }' \
    --response-templates '{"application/json": ""}' \
    2>/dev/null || true
}

# Enable CORS on all resources
enable_cors $START_ID "/transfer/start"
enable_cors $STATUS_DETAIL_ID "/transfer/status/{id}"
enable_cors $HISTORY_ID "/transfer/history"

echo "✅ CORS enabled on all endpoints"
echo ""

# ============================================================================
# Step 11: Deploy API to prod stage
# ============================================================================
echo "🔧 [11/11] Deploying API to prod stage..."

aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --description "Initial deployment of FileFerry API"

echo "✅ API deployed to prod stage"
echo ""

# ============================================================================
# Deployment Complete
# ============================================================================
echo "=========================================="
echo "🎉 API Gateway Deployment Complete!"
echo "=========================================="
echo ""
echo "📋 API Details:"
echo "   API ID: $API_ID"
echo "   Region: us-east-1"
echo "   Stage: prod"
echo ""
echo "🌐 API Gateway URL:"
echo "   https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod"
echo ""
echo "🔗 Endpoints:"
echo "   POST   /transfer/start"
echo "   GET    /transfer/status/{id}"
echo "   GET    /transfer/history"
echo ""
echo "📝 Next Steps:"
echo "   1. Copy the API Gateway URL above"
echo "   2. Update demo.html with this URL"
echo "   3. Test endpoints with curl or Postman"
echo "   4. Configure ServiceNow environment variables in Lambda"
echo ""
echo "✅ Your API is ready to use!"
echo ""

EOF

# Make executable
chmod +x deploy-api-gateway.sh

echo "✅ Script created successfully!"
```

**Option B: Upload File Method**

1. In CloudShell, click **Actions** → **Upload file**
2. Select `DEPLOY_API_GATEWAY.sh` from your local computer
3. Make it executable:
```bash
chmod +x DEPLOY_API_GATEWAY.sh
```

---

### **Step 3: Run Deployment Script** (10 minutes)

```bash
# Execute the deployment script
./deploy-api-gateway.sh
```

**What happens during deployment:**
- ✅ Creates REST API "FileFerry-API"
- ✅ Creates 3 resources with path structure
- ✅ Creates IAM role for API Gateway
- ✅ Configures Step Functions integration
- ✅ Configures Lambda proxy integrations
- ✅ Enables CORS on all endpoints
- ✅ Deploys to prod stage

**Expected output:**
```
🚀 Starting FileFerry API Gateway Deployment...
Region: us-east-1
Account: 637423332185

[1/11] Creating REST API...
✅ API Created: abc123xyz

[2/11] Creating /transfer resource...
✅ /transfer created

[3/11] Creating /transfer/start resource...
✅ /transfer/start created

...

🎉 API Gateway Deployment Complete!
🌐 API Gateway URL:
   https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod
```

---

### **Step 4: Copy API Gateway URL** (1 minute)

**IMPORTANT:** Copy the complete API Gateway URL from the output:

```
https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod
```

You'll need this for:
- ✅ Updating demo.html
- ✅ Testing endpoints
- ✅ Configuring Teams bot

---

### **Step 5: Test API Endpoints** (5 minutes)

**Test 1: POST /transfer/start**

```bash
# In CloudShell
curl -X POST https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod/transfer/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test@example.com",
    "transfer_plan": {
      "source_bucket": "your-bucket-name",
      "source_key": "test-file.txt",
      "destination_host": "ftp.example.com",
      "destination_port": 21,
      "destination_user": "ftpuser",
      "destination_password": "ftppass",
      "destination_path": "/uploads/",
      "transfer_type": "ftp"
    },
    "servicenow_tickets": ["INC0010001", "INC0010002"]
  }'
```

**Expected response:**
```json
{
  "executionArn": "arn:aws:states:us-east-1:637423332185:execution:FileFerryTransferStateMachine:abc123",
  "startDate": 1234567890.123
}
```

**Test 2: GET /transfer/history**

```bash
curl https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod/transfer/history
```

**Expected response:**
```json
{
  "transfers": [],
  "count": 0
}
```

---

## ⚙️ Post-Deployment Configuration

### **Configure ServiceNow Environment Variables**

Your Lambda function needs ServiceNow credentials to update tickets.

**In AWS Console:**

1. Go to **Lambda** → **FileFerry-UpdateServiceNow**
2. Click **Configuration** → **Environment variables**
3. Click **Edit** → **Add environment variable**

Add these 3 variables:

| Key | Value | Example |
|-----|-------|---------|
| `SERVICENOW_INSTANCE_URL` | Your ServiceNow instance URL | `https://dev12345.service-now.com` |
| `SERVICENOW_USERNAME` | Your ServiceNow username | `admin` |
| `SERVICENOW_PASSWORD` | Your ServiceNow password | `your-password` |

4. Click **Save**

---

## 🧪 Verification Checklist

After deployment, verify:

```bash
# 1. Check API Gateway exists
aws apigateway get-rest-apis --query 'items[?name==`FileFerry-API`]'

# 2. Check endpoints
aws apigateway get-resources --rest-api-id YOUR-API-ID

# 3. Check IAM role
aws iam get-role --role-name APIGatewayStepFunctionsRole

# 4. Test POST /transfer/start endpoint
curl -X POST https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod/transfer/start \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

---

## 🚨 Troubleshooting

### **Error: "Missing Authentication Token"**

**Cause:** Wrong URL or endpoint path

**Fix:**
- Verify URL format: `https://API-ID.execute-api.us-east-1.amazonaws.com/prod/transfer/start`
- Check endpoint exists: `aws apigateway get-resources --rest-api-id YOUR-API-ID`

---

### **Error: "Internal Server Error"**

**Cause:** Lambda permission or Step Functions integration issue

**Fix:**
```bash
# Check Lambda permissions
aws lambda get-policy --function-name FileFerry-GetTransferStatus

# Re-add permission
aws lambda add-permission \
  --function-name FileFerry-GetTransferStatus \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:637423332185:YOUR-API-ID/*/*"
```

---

### **Error: "CORS Error" in Browser**

**Cause:** CORS headers not configured properly

**Fix:**
```bash
# Re-enable CORS
aws apigateway update-integration-response \
  --rest-api-id YOUR-API-ID \
  --resource-id RESOURCE-ID \
  --http-method POST \
  --status-code 200 \
  --patch-operations op=replace,path=/responseParameters/method.response.header.Access-Control-Allow-Origin,value="'*'"

# Redeploy API
aws apigateway create-deployment \
  --rest-api-id YOUR-API-ID \
  --stage-name prod
```

---

## 📊 What You'll Have After Deployment

```
✅ API Gateway REST API: FileFerry-API
✅ 3 Endpoints:
   - POST   /transfer/start      → Triggers Step Functions
   - GET    /transfer/status/{id} → Query transfer status
   - GET    /transfer/history     → List all transfers
✅ CORS enabled on all endpoints
✅ IAM role: APIGatewayStepFunctionsRole
✅ Lambda permissions configured
✅ Deployed to prod stage
✅ API URL: https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod
```

---

## 🎯 Next Steps

After API Gateway is deployed:

1. ✅ **Update demo.html** with API Gateway URL (5 min)
2. ✅ **Configure ServiceNow credentials** in Lambda (2 min)
3. ✅ **Test end-to-end flow** in browser (10 min)
4. ✅ **Add Teams bot** (optional, 10 min)

---

## 📞 Need Help?

If you encounter any issues during deployment:

1. Check CloudShell output for error messages
2. Verify you're in **us-east-1** region
3. Confirm all 14 Lambda functions are deployed
4. Check IAM permissions for your AWS user
5. Review troubleshooting section above

---

**Ready to deploy? Follow Step 1 above! 🚀**
