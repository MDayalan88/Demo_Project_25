# API Gateway Deployment Guide

## 🎯 Overview
Create REST API to expose FileFerry workflow to frontend applications.

## 📋 Current Progress: 85% Complete
- ✅ 14 Lambda functions deployed
- ✅ Step Functions State Machine working
- 🔄 API Gateway (Next - 30 minutes)
- ⏳ Frontend integration (1 hour)

---

## 🚀 Quick Deploy: AWS Console (Recommended)

### Step 1: Create REST API (5 minutes)

1. **Go to API Gateway Console**
   ```
   https://us-east-1.console.aws.amazon.com/apigateway/main/apis?region=us-east-1
   ```

2. **Create API**
   - Click "Create API"
   - Choose "REST API" (not private)
   - Click "Build"
   - API name: `FileFerry-API`
   - Description: `File transfer orchestration API`
   - Endpoint Type: Regional
   - Click "Create API"

### Step 2: Create Resources & Methods (15 minutes)

#### Resource 1: /transfer

1. Click "Create Resource"
   - Resource Name: `transfer`
   - Resource Path: `transfer`
   - Enable CORS: ✅ Check
   - Click "Create Resource"

#### Method 1: POST /transfer/start

1. Select `/transfer` resource
2. Click "Create Method"
3. Method type: `POST`
4. Integration type: `AWS Service`
5. AWS Region: `us-east-1`
6. AWS Service: `Step Functions`
7. HTTP method: `POST`
8. Action: `StartExecution`
9. Execution role: Create new role (or use existing with Step Functions permissions)
   - Role ARN: `arn:aws:iam::637423332185:role/APIGatewayStepFunctionsRole`
10. Click "Create Method"

**Integration Request Mapping Template:**
- Content-Type: `application/json`
- Template:
```json
{
  "stateMachineArn": "arn:aws:states:us-east-1:637423332185:stateMachine:FileFerry-TransferStateMachine",
  "input": "$util.escapeJavaScript($input.json('$'))"
}
```

#### Method 2: GET /transfer/status/{id}

1. Create child resource under `/transfer`
   - Resource Name: `status`
   - Resource Path: `status`
2. Create child resource under `/transfer/status`
   - Resource Name: `{id}`
   - Resource Path: `{id}`
3. Select `/transfer/status/{id}` resource
4. Create Method: `GET`
5. Integration type: `Lambda Function`
6. Lambda Function: `FileFerry-API-Get-Status`
7. Click "Create Method"

#### Method 3: GET /transfer/history

1. Create resource under `/transfer`
   - Resource Name: `history`
   - Resource Path: `history`
2. Select `/transfer/history` resource
3. Create Method: `GET`
4. Integration type: `Lambda Function`
5. Lambda Function: `FileFerry-API-Get-History`
6. Click "Create Method"

### Step 3: Enable CORS (5 minutes)

For **each** resource (`/transfer`, `/transfer/status/{id}`, `/transfer/history`):

1. Select the resource
2. Click "Enable CORS"
3. Access-Control-Allow-Origin: `*` (or your frontend domain)
4. Access-Control-Allow-Headers: `Content-Type,X-Amz-Date,Authorization,X-Api-Key`
5. Access-Control-Allow-Methods: Select `GET`, `POST`, `OPTIONS`
6. Click "Save"

### Step 4: Deploy API (5 minutes)

1. Click "Deploy API" button
2. Deployment stage: `[New Stage]`
3. Stage name: `prod`
4. Stage description: `Production deployment`
5. Click "Deploy"

**🎉 Your API is live!**

Note the Invoke URL: `https://xxxxxxxx.execute-api.us-east-1.amazonaws.com/prod`

---

## 🔧 Alternative: AWS CLI (CloudShell)

```bash
export ACCOUNT_ID=637423332185
export REGION=us-east-1
export API_NAME="FileFerry-API"

# Step 1: Create REST API
API_ID=$(aws apigateway create-rest-api \
    --name $API_NAME \
    --description "FileFerry transfer orchestration API" \
    --endpoint-configuration types=REGIONAL \
    --query 'id' --output text)

echo "✅ API created: $API_ID"

# Step 2: Get root resource ID
ROOT_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --query 'items[?path==`/`].id' \
    --output text)

# Step 3: Create /transfer resource
TRANSFER_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part transfer \
    --query 'id' --output text)

# Step 4: Create /transfer/start resource
START_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $TRANSFER_ID \
    --path-part start \
    --query 'id' --output text)

# Step 5: Create POST method on /transfer/start
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $START_ID \
    --http-method POST \
    --authorization-type NONE

# Step 6: Create Lambda integration for /transfer/start
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $START_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:FileFerry-API-Start-Transfer/invocations

# Step 7: Create /transfer/status resource
STATUS_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $TRANSFER_ID \
    --path-part status \
    --query 'id' --output text)

# Step 8: Create /transfer/status/{id} resource
STATUS_PARAM_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $STATUS_ID \
    --path-part '{id}' \
    --query 'id' --output text)

# Step 9: Create GET method on /transfer/status/{id}
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $STATUS_PARAM_ID \
    --http-method GET \
    --authorization-type NONE

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $STATUS_PARAM_ID \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:FileFerry-API-Get-Status/invocations

# Step 10: Create /transfer/history resource
HISTORY_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $TRANSFER_ID \
    --path-part history \
    --query 'id' --output text)

# Step 11: Create GET method on /transfer/history
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $HISTORY_ID \
    --http-method GET \
    --authorization-type NONE

aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $HISTORY_ID \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:FileFerry-API-Get-History/invocations

# Step 12: Deploy API
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --description "Production deployment"

echo ""
echo "🎉 API Gateway deployed!"
echo "📍 Invoke URL: https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod"
echo ""
echo "Test endpoints:"
echo "  POST https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/transfer/start"
echo "  GET  https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/transfer/status/{id}"
echo "  GET  https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/transfer/history"
```

---

## 🧪 Test API Endpoints

### Test POST /transfer/start

```bash
export API_ID=<YOUR_API_ID>
export REGION=us-east-1

curl -X POST \
  https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/transfer/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test@example.com",
    "servicenow_tickets": ["INC0010001", "RITM0010001"],
    "s3_bucket": "fileferry-source-bucket",
    "s3_key": "test-files/sample.txt",
    "ftp_host": "ftp.example.com",
    "ftp_user": "testuser",
    "ftp_password": "testpass123",
    "ftp_path": "/uploads/sample.txt",
    "protocol": "sftp"
  }'
```

**Expected Response:**
```json
{
  "executionArn": "arn:aws:states:us-east-1:637423332185:execution:FileFerry-TransferStateMachine:xxx",
  "startDate": "2025-12-05T..."
}
```

### Test GET /transfer/status/{id}

```bash
curl https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/transfer/status/abc123
```

### Test GET /transfer/history

```bash
curl https://${API_ID}.execute-api.${REGION}.amazonaws.com/prod/transfer/history
```

---

## 🔐 IAM Role for API Gateway → Step Functions

If you need to create the IAM role manually:

### Trust Policy
```json
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
```

### Permissions Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "states:StartExecution"
      ],
      "Resource": "arn:aws:states:us-east-1:637423332185:stateMachine:FileFerry-TransferStateMachine"
    }
  ]
}
```

**Create role:**
```bash
# Create role
aws iam create-role \
    --role-name APIGatewayStepFunctionsRole \
    --assume-role-policy-document file://trust-policy.json

# Attach inline policy
aws iam put-role-policy \
    --role-name APIGatewayStepFunctionsRole \
    --policy-name StepFunctionsExecutionPolicy \
    --policy-document file://permissions-policy.json

# Give Lambda invoke permissions
aws lambda add-permission \
    --function-name FileFerry-API-Start-Transfer \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com
```

---

## 📊 API Endpoint Summary

| Method | Endpoint | Lambda/Service | Purpose |
|--------|----------|----------------|---------|
| POST | `/transfer/start` | Step Functions | Start file transfer workflow |
| GET | `/transfer/status/{id}` | FileFerry-API-Get-Status | Get transfer status |
| GET | `/transfer/history` | FileFerry-API-Get-History | List transfer history |

---

## 🎯 After API Gateway Deployment

1. **Copy the Invoke URL** from API Gateway console
   - Format: `https://xxxxxxxx.execute-api.us-east-1.amazonaws.com/prod`

2. **Update Frontend Configuration**
   - File: `frontend/src/config.js` or `frontend/config.yaml`
   - Replace mock API URL with real API Gateway URL

3. **Test End-to-End**
   - Open frontend in browser
   - Submit a transfer request
   - Watch it flow: Frontend → API Gateway → Step Functions → Lambda

---

## ✅ Success Criteria

- [ ] API Gateway REST API created
- [ ] 3 endpoints configured with Lambda/Step Functions integration
- [ ] CORS enabled on all endpoints
- [ ] API deployed to `prod` stage
- [ ] Test POST /transfer/start successfully starts Step Functions execution
- [ ] Test GET endpoints return data from DynamoDB
- [ ] Invoke URL ready for frontend integration

**Estimated Time: 30 minutes**

**Next: Update frontend with API URL → 100% Complete!** 🎉
