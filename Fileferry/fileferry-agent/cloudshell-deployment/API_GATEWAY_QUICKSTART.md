# 🚀 API Gateway Deployment - Quick Start Guide

## 📋 What We'll Deploy

API Gateway with 3 endpoints:
1. **POST /transfer/start** → Triggers Step Functions workflow
2. **GET /transfer/status/{id}** → Gets transfer status
3. **GET /transfer/history** → Lists all transfers

**Time Required**: 10-15 minutes (automated script)

---

## ✅ Prerequisites (Already Complete!)

- ✅ AWS Account ID: 637423332185
- ✅ Region: us-east-1
- ✅ 14 Lambda functions deployed
- ✅ Step Functions state machine active
- ✅ IAM roles configured

---

## 🎯 Option 1: Automated CloudShell Deployment (RECOMMENDED - 10 min)

### Step 1: Open AWS CloudShell

1. Go to AWS Console: https://console.aws.amazon.com
2. Click CloudShell icon (top right, looks like >_ )
3. Wait for CloudShell to initialize (~30 seconds)

### Step 2: Upload Deployment Script

**Option A: Copy-Paste Method (Easier)**

```bash
# Create the deployment script
cat > deploy-api-gateway.sh << 'SCRIPT_END'
```

Then paste the **entire contents** of `DEPLOY_API_GATEWAY.sh` and press Enter, then type:

```bash
SCRIPT_END
```

**Option B: Upload Method**

1. In CloudShell, click "Actions" → "Upload file"
2. Select `DEPLOY_API_GATEWAY.sh` from your local machine
3. Wait for upload to complete

### Step 3: Make Script Executable & Run

```bash
# Make executable
chmod +x deploy-api-gateway.sh

# Run deployment
./deploy-api-gateway.sh
```

### Step 4: Monitor Deployment

You'll see progress updates:
```
Step 1: Creating REST API...
✓ API created: abc123xyz

Step 2: Creating /transfer resource...
✓ /transfer resource created

...

✅ API Gateway Deployment Complete!
```

**Total time: ~10 minutes**

### Step 5: Copy Your API URL

At the end, you'll see:
```
🌐 API Endpoint URLs:
  • Base URL: https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod
```

**SAVE THIS URL!** You'll need it for frontend integration.

---

## 🎯 Option 2: Manual AWS Console Deployment (30 min)

If you prefer manual setup, follow the detailed guide in `API_GATEWAY_DEPLOYMENT.md`.

### Quick Steps:

1. **Create REST API** (5 min)
   - Go to API Gateway Console
   - Create API → REST API
   - Name: FileFerry-API
   
2. **Create Resources** (10 min)
   - /transfer
   - /transfer/start
   - /transfer/status/{id}
   - /transfer/history

3. **Create Methods** (10 min)
   - POST /transfer/start → Step Functions integration
   - GET /transfer/status/{id} → Lambda integration
   - GET /transfer/history → Lambda integration

4. **Enable CORS** (3 min)
   - Enable on all resources

5. **Deploy to prod** (2 min)
   - Create deployment
   - Stage name: prod

---

## 🧪 Testing Your API Gateway

### Test 1: POST /transfer/start

```bash
# Replace YOUR-API-ID with your actual API ID
export API_ID="YOUR-API-ID"

# Test transfer
curl -X POST \
  "https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod/transfer/start" \
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
  "executionArn": "arn:aws:states:us-east-1:637423332185:execution:FileFerry-TransferStateMachine:...",
  "startDate": "2025-12-05T..."
}
```

### Test 2: GET /transfer/status/{id}

```bash
# Use executionArn from previous test
curl "https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod/transfer/status/EXECUTION-ARN-HERE"
```

**Expected Response:**
```json
{
  "status": "SUCCEEDED",
  "output": {
    "request_id": "req_123",
    "transfer_success": true
  }
}
```

### Test 3: GET /transfer/history

```bash
curl "https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod/transfer/history"
```

**Expected Response:**
```json
{
  "transfers": [
    {
      "request_id": "req_123",
      "user_id": "test@example.com",
      "status": "COMPLETED",
      "timestamp": "2025-12-05T10:30:00Z"
    }
  ]
}
```

---

## 🔧 Troubleshooting

### Issue 1: "Missing Authentication Token"

**Cause**: Wrong URL or missing path

**Fix**: Check you're using the correct URL format:
```
https://API-ID.execute-api.us-east-1.amazonaws.com/prod/transfer/start
                                                    ^^^^
                                                Must include /prod
```

### Issue 2: "Internal Server Error"

**Cause**: Lambda function or Step Functions issue

**Fix**: Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/FileFerry-API-Get-Status --follow
```

### Issue 3: CORS Error in Browser

**Cause**: CORS not enabled properly

**Fix**: Re-run CORS configuration:
```bash
# In CloudShell
aws apigateway put-integration-response \
  --rest-api-id YOUR-API-ID \
  --resource-id RESOURCE-ID \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Origin": "'"'"'*'"'"'"}'
```

### Issue 4: "Execution role ARN is invalid"

**Cause**: IAM role not ready

**Fix**: Wait 10 seconds and retry:
```bash
sleep 10
./deploy-api-gateway.sh
```

---

## 📊 Verify Deployment

### Check 1: API Gateway Console

```
https://us-east-1.console.aws.amazon.com/apigateway/main/apis?region=us-east-1
```

You should see:
- ✅ FileFerry-API
- ✅ 3 resources
- ✅ 3 methods (POST, GET, GET)
- ✅ Stage: prod

### Check 2: Test in Console

1. Go to API Gateway → FileFerry-API
2. Select "POST /transfer/start"
3. Click "Test"
4. Paste test JSON
5. Click "Test" button
6. Should see 200 response

### Check 3: CloudWatch Logs

```bash
# Check API Gateway logs
aws logs describe-log-groups --log-group-name-prefix /aws/apigateway

# Check Lambda logs
aws logs tail /aws/lambda/FileFerry-API-Get-Status --follow
```

---

## 📝 Save Your API Details

Create a file to save your API information:

```bash
# In CloudShell
cat > ~/api-details.txt << EOF
FileFerry API Gateway Details
==============================
API ID: ${API_ID}
Base URL: https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod
Region: us-east-1
Stage: prod
Deployed: $(date)

Endpoints:
1. POST /transfer/start
   https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod/transfer/start

2. GET /transfer/status/{id}
   https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod/transfer/status/{id}

3. GET /transfer/history
   https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod/transfer/history
EOF

cat ~/api-details.txt
```

---

## ✅ Deployment Complete Checklist

- [ ] API Gateway created with ID
- [ ] 3 resources created (/transfer/start, /status/{id}, /history)
- [ ] 3 methods configured (POST, GET, GET)
- [ ] CORS enabled on all endpoints
- [ ] Deployed to prod stage
- [ ] Base URL obtained
- [ ] Test POST /transfer/start successful
- [ ] Test GET /transfer/status successful
- [ ] Test GET /transfer/history successful
- [ ] API URL saved for frontend integration

---

## 🎉 Next Steps

After API Gateway is deployed:

1. **Update Frontend** (5 minutes)
   - Edit `frontend/demo.html`
   - Add API_BASE_URL constant
   - Replace mock functions with real API calls

2. **Test End-to-End** (10 minutes)
   - Open demo.html in browser
   - Submit file transfer
   - Verify workflow completes

3. **Celebrate!** 🎊
   - FileFerry is 100% deployed!
   - You have a fully functional file transfer system!

---

## 📞 Need Help?

If you encounter issues:

1. Check CloudWatch Logs
2. Verify IAM permissions
3. Test individual Lambda functions
4. Check Step Functions execution history
5. Review API Gateway execution logs

**You're almost there! Let's deploy this API Gateway! 🚀**
