# 🧪 API Gateway Testing Guide

## ✅ Your Deployed API

**API Gateway URL:** `https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod`

**API ID:** `gwosr3m399`

**Region:** `us-east-1`

**Stage:** `prod`

---

## 🔗 Available Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/transfer/start` | Start a new file transfer |
| GET | `/transfer/status/{id}` | Get transfer status by execution ID |
| GET | `/transfer/history` | List all recent transfers |

---

## 🧪 Test 1: Check API Gateway Health

### **Test GET /transfer/history** (Simplest test)

**In AWS CloudShell:**
```bash
curl https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod/transfer/history
```

**Expected Response:**
```json
{
  "transfers": [],
  "count": 0,
  "message": "No transfers found"
}
```

**In PowerShell (Windows):**
```powershell
Invoke-RestMethod -Uri "https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod/transfer/history" -Method Get
```

✅ **Success:** If you get a response (even empty), API Gateway is working!

❌ **Error:** If you get "Missing Authentication Token" → Check URL spelling

---

## 🧪 Test 2: Start a Transfer (Real Test)

### **Option A: Using Test Input File**

**In AWS CloudShell:**
```bash
# Create test input
cat > test_transfer.json << 'EOF'
{
  "user_id": "test@example.com",
  "transfer_plan": {
    "source_bucket": "your-actual-bucket-name",
    "source_key": "test-file.txt",
    "destination_host": "ftp.example.com",
    "destination_port": 21,
    "destination_user": "ftpuser",
    "destination_password": "ftppass",
    "destination_path": "/uploads/",
    "transfer_type": "ftp"
  },
  "servicenow_tickets": ["INC0010001", "INC0010002"]
}
EOF

# Test the API
curl -X POST https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod/transfer/start \
  -H "Content-Type: application/json" \
  -d @test_transfer.json
```

**Expected Response:**
```json
{
  "executionArn": "arn:aws:states:us-east-1:637423332185:execution:FileFerryTransferStateMachine:abc123...",
  "startDate": 1234567890.123
}
```

### **Option B: Using PowerShell (Windows)**

```powershell
$body = @{
    user_id = "test@example.com"
    transfer_plan = @{
        source_bucket = "your-actual-bucket-name"
        source_key = "test-file.txt"
        destination_host = "ftp.example.com"
        destination_port = 21
        destination_user = "ftpuser"
        destination_password = "ftppass"
        destination_path = "/uploads/"
        transfer_type = "ftp"
    }
    servicenow_tickets = @("INC0010001", "INC0010002")
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod/transfer/start" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

## 🧪 Test 3: Check Transfer Status

After starting a transfer, you'll get an `executionArn`. Use it to check status:

**Extract Execution ID from ARN:**
```
executionArn: arn:aws:states:us-east-1:637423332185:execution:FileFerryTransferStateMachine:abc123-def456
                                                                                              ↑
                                                                                    Execution ID
```

**Test GET /transfer/status/{id}:**

**In AWS CloudShell:**
```bash
# Replace abc123-def456 with your actual execution ID
curl https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod/transfer/status/abc123-def456
```

**In PowerShell:**
```powershell
$executionId = "abc123-def456"  # Replace with your execution ID
Invoke-RestMethod -Uri "https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod/transfer/status/$executionId" -Method Get
```

**Expected Response:**
```json
{
  "execution_id": "abc123-def456",
  "status": "RUNNING",
  "start_time": "2025-12-05T10:30:00Z",
  "progress": "Downloading from S3...",
  "percent_complete": 25
}
```

---

## 🔍 Verify API in AWS Console

### **1. View API Gateway Dashboard**

Open: https://us-east-1.console.aws.amazon.com/apigateway/main/apis/gwosr3m399?region=us-east-1

**You should see:**
- API Name: **FileFerry-API**
- Stage: **prod**
- Resources: `/transfer/start`, `/transfer/status/{id}`, `/transfer/history`

### **2. View API Stages**

1. Click **FileFerry-API**
2. Click **Stages** (left menu)
3. Click **prod**
4. You'll see **Invoke URL**: `https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod`

### **3. View API Resources**

1. Click **Resources** (left menu)
2. You'll see the resource tree:
   ```
   /
   └── /transfer
       ├── /start (POST)
       ├── /status
       │   └── /{id} (GET)
       └── /history (GET)
   ```

### **4. Test in API Gateway Console**

1. Click **Resources** → **POST /transfer/start**
2. Click **Test** button (lightning bolt icon)
3. Paste test JSON in **Request Body**
4. Click **Test**
5. See response in **Response Body**

---

## 🧪 Quick Test Script

**Copy this to AWS CloudShell for quick testing:**

```bash
#!/bin/bash

API_URL="https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod"

echo "🧪 Testing FileFerry API Gateway..."
echo ""

# Test 1: Health check (GET /transfer/history)
echo "Test 1: GET /transfer/history"
echo "Command: curl $API_URL/transfer/history"
curl -s $API_URL/transfer/history | jq '.'
echo ""

# Test 2: POST /transfer/start (will fail without valid S3 bucket)
echo "Test 2: POST /transfer/start"
echo "Command: curl -X POST $API_URL/transfer/start"
curl -s -X POST $API_URL/transfer/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test@example.com",
    "transfer_plan": {
      "source_bucket": "test-bucket",
      "source_key": "test.txt",
      "destination_host": "ftp.example.com"
    },
    "servicenow_tickets": ["INC001", "INC002"]
  }' | jq '.'
echo ""

echo "✅ API Gateway is responding!"
```

**Run it:**
```bash
chmod +x test-api.sh
./test-api.sh
```

---

## 📊 Monitoring & Logs

### **1. View API Gateway Logs**

1. Go to **CloudWatch** → **Log groups**
2. Search for: `/aws/apigateway/FileFerry-API`
3. View recent requests and responses

### **2. View Step Functions Executions**

1. Go to **Step Functions** → **State machines**
2. Click **FileFerryTransferStateMachine**
3. View **Executions** tab
4. Click on any execution to see details

### **3. View Lambda Logs**

1. Go to **CloudWatch** → **Log groups**
2. Search for: `/aws/lambda/FileFerry-*`
3. View logs for each Lambda function

---

## 🚨 Troubleshooting

### **Error: "Missing Authentication Token"**

**Cause:** Wrong URL or typo in endpoint path

**Fix:**
```bash
# Correct URLs:
✅ https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod/transfer/start
✅ https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod/transfer/history

# Wrong URLs (will fail):
❌ https://gwosr3m399.execute-api.us-east-1.amazonaws.com/transfer/start  # Missing /prod
❌ https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod/start      # Wrong path
```

---

### **Error: "Internal Server Error"**

**Cause:** Step Functions or Lambda error

**Fix:**
1. Check Step Functions execution in AWS Console
2. View Lambda logs in CloudWatch
3. Verify IAM permissions

**Debug Command:**
```bash
# Check Step Functions execution
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:637423332185:stateMachine:FileFerryTransferStateMachine \
  --max-results 5
```

---

### **Error: "S3 bucket not found"**

**Cause:** Invalid S3 bucket name in request

**Fix:**
Replace `"source_bucket": "test-bucket"` with your actual S3 bucket name

**List your S3 buckets:**
```bash
aws s3 ls
```

---

### **Error: "CORS Error" in Browser**

**Cause:** CORS not enabled properly

**Fix:**
```bash
# Check CORS configuration
aws apigateway get-integration-response \
  --rest-api-id gwosr3m399 \
  --resource-id <RESOURCE-ID> \
  --http-method POST \
  --status-code 200
```

CORS is already configured in your API, but if issues persist:
```bash
# Redeploy API
aws apigateway create-deployment \
  --rest-api-id gwosr3m399 \
  --stage-name prod \
  --description "CORS fix"
```

---

## 🎯 Next Steps

After confirming API works:

### **1. Configure ServiceNow Credentials**

In AWS Lambda Console:
1. Go to **FileFerry-UpdateServiceNow** Lambda
2. **Configuration** → **Environment variables** → **Edit**
3. Add:
   - `SERVICENOW_INSTANCE_URL` = Your instance URL
   - `SERVICENOW_USERNAME` = Your username
   - `SERVICENOW_PASSWORD` = Your password

### **2. Update demo.html**

Replace the API URL in `demo.html`:
```javascript
const API_BASE_URL = 'https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod';
```

### **3. Test End-to-End**

1. Open `demo.html` in browser
2. Fill out transfer form with real S3 bucket
3. Submit and watch real-time progress
4. Verify ServiceNow tickets updated

### **4. Add Teams Bot (Optional)**

Set bot endpoint to:
```
https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod/api/messages
```

---

## ✅ Success Checklist

- [ ] GET /transfer/history returns response
- [ ] POST /transfer/start accepts request
- [ ] API visible in AWS Console
- [ ] Step Functions execution starts
- [ ] Lambda functions execute
- [ ] CloudWatch logs show activity
- [ ] ServiceNow credentials configured
- [ ] demo.html updated with API URL
- [ ] End-to-end test successful

---

## 📞 Quick Commands Reference

```bash
# Test API health
curl https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod/transfer/history

# Start transfer
curl -X POST https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod/transfer/start \
  -H "Content-Type: application/json" \
  -d @test_input.json

# Check status
curl https://gwosr3m399.execute-api.us-east-1.amazonaws.com/prod/transfer/status/EXECUTION-ID

# View API in console
https://us-east-1.console.aws.amazon.com/apigateway/main/apis/gwosr3m399

# View Step Functions
https://us-east-1.console.aws.amazon.com/states/home?region=us-east-1#/statemachines

# View Lambda functions
https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions
```

---

**Your API is ready! Start testing! 🚀**
