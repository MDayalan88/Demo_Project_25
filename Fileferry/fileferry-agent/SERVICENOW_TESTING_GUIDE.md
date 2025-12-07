# 🧪 ServiceNow Integration Testing Guide

## ✅ You've Configured ServiceNow Credentials

**Lambda Function:** `FileFerry-UpdateServiceNow`

**Environment Variables Set:**
- `SERVICENOW_INSTANCE_URL` = Your ServiceNow instance URL
- `SERVICENOW_USERNAME` = Your username
- `SERVICENOW_PASSWORD` = Your password

---

## 🔍 How to Verify ServiceNow Integration

### **Method 1: Quick Lambda Test (Recommended)**

Test the Lambda function directly to verify credentials work.

**In AWS Lambda Console:**

1. Go to **Lambda** → **FileFerry-UpdateServiceNow**
2. Click **Test** tab
3. Create a new test event with this JSON:

```json
{
  "servicenow_tickets": ["INC0010001", "INC0010002"],
  "transfer_result": {
    "status": "completed",
    "bytes_transferred": 1048576,
    "remote_path": "/uploads/test-file.txt",
    "md5_checksum": "abc123def456",
    "completed_at": "2025-12-05T10:30:00Z"
  }
}
```

4. Click **Test** button
5. **Check Result:**

**✅ Success Response:**
```json
{
  "status": "completed",
  "tickets_updated": 2,
  "updates": [
    {
      "ticket": "INC0010001",
      "status": "updated"
    },
    {
      "ticket": "INC0010002",
      "status": "updated"
    }
  ]
}
```

**❌ If Failed:**
- Check error message in execution result
- Verify credentials are correct
- Verify instance URL format: `https://devXXXXX.service-now.com` (no trailing slash)
- Check ServiceNow instance is accessible

---

### **Method 2: Test via PowerShell Script**

Create a quick test to verify ServiceNow credentials from your local machine:

```powershell
# ServiceNow Connection Test
$instanceUrl = "https://devXXXXX.service-now.com"  # Your instance URL
$username = "your-username"
$password = "your-password"

# Create base64 auth header
$base64Auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${username}:${password}"))

Write-Host "🧪 Testing ServiceNow Connection..." -ForegroundColor Cyan
Write-Host "Instance: $instanceUrl`n" -ForegroundColor Gray

try {
    # Test connection by querying incidents
    $response = Invoke-RestMethod -Uri "$instanceUrl/api/now/table/incident?sysparm_limit=1" `
        -Method Get `
        -Headers @{
            Authorization = "Basic $base64Auth"
            'Content-Type' = 'application/json'
        }
    
    Write-Host "✅ SUCCESS!" -ForegroundColor Green
    Write-Host "ServiceNow connection working!" -ForegroundColor Green
    Write-Host "`nRetrieved incident count: $($response.result.Count)`n" -ForegroundColor Gray
}
catch {
    Write-Host "❌ FAILED!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)`n" -ForegroundColor Red
    
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "❌ Authentication Failed - Check username/password" -ForegroundColor Yellow
    }
    elseif ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "❌ Instance not found - Check instance URL" -ForegroundColor Yellow
    }
}
```

---

### **Method 3: Test via CloudShell (AWS CLI)**

Test the Lambda function using AWS CLI:

```bash
# In AWS CloudShell

# Create test event file
cat > test-servicenow.json << 'EOF'
{
  "servicenow_tickets": ["INC0010001", "INC0010002"],
  "transfer_result": {
    "status": "completed",
    "bytes_transferred": 1048576,
    "remote_path": "/uploads/test-file.txt",
    "md5_checksum": "abc123def456",
    "completed_at": "2025-12-05T10:30:00Z"
  }
}
EOF

# Invoke Lambda function
aws lambda invoke \
  --function-name FileFerry-UpdateServiceNow \
  --payload file://test-servicenow.json \
  --region us-east-1 \
  response.json

# View result
cat response.json | jq '.'
```

**Expected Output:**
```json
{
  "status": "completed",
  "tickets_updated": 2,
  "updates": [...]
}
```

---

### **Method 4: Create Test Tickets in ServiceNow**

Before testing integration, create actual test tickets:

**In ServiceNow Developer Portal:**

1. Go to **Incident** → **Create New**
2. Fill in:
   - **Short Description**: "FileFerry Test Transfer - User Ticket"
   - **Assignment Group**: "DataOps"
   - **Priority**: "3 - Moderate"
3. Click **Submit**
4. **Copy the Incident Number** (e.g., INC0010001)

5. Create second ticket:
   - **Short Description**: "FileFerry Test Transfer - Audit Ticket"
   - **Assignment Group**: "DataOps"
   - **Priority**: "4 - Low"
6. Click **Submit**
7. **Copy the Incident Number** (e.g., INC0010002)

Now you have real tickets to test with!

---

### **Method 5: End-to-End Test with demo.html**

Test the complete flow including ServiceNow updates:

**Prerequisites:**
- ServiceNow credentials configured in Lambda ✅
- Real ServiceNow tickets created (INC numbers)
- Valid S3 bucket with a test file

**Steps:**

1. **Start demo.html:**
   ```powershell
   cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend
   python -m http.server 8000
   ```

2. **Open browser:** `http://localhost:8000/demo.html`

3. **Fill out transfer form:**
   - Assignment Group: DataOps
   - Environment: PROD
   - AWS Region: us-east-1
   - Bucket Name: `your-actual-bucket`
   - File Name: `test-file.txt`
   - Priority: High

4. **Click "Continue to AWS SSO"**

5. **Note the ServiceNow tickets shown** (or use your real ones)

6. **Click "Initiate Transfer"**

7. **Watch the progress**

8. **Check ServiceNow:**
   - Go to ServiceNow portal
   - Open the incident tickets
   - Look for **Work Notes** with transfer completion details
   - Ticket **State** should change to "Resolved"

---

## 🔍 What to Look For in ServiceNow

After a successful transfer, your ServiceNow tickets should show:

**Work Notes:**
```
Transfer Completed Successfully

Bytes Transferred: 1048576
Remote Path: /uploads/test-file.txt
MD5 Checksum: abc123def456
Completed At: 2025-12-05T10:30:00Z
```

**State Change:**
- Before: "New" or "In Progress"
- After: "Resolved" (State = 6)

---

## 🚨 Troubleshooting

### **Error: "401 Unauthorized"**
**Cause:** Wrong username or password

**Fix:**
1. Go to AWS Lambda → FileFerry-UpdateServiceNow
2. Configuration → Environment variables
3. Verify `SERVICENOW_USERNAME` and `SERVICENOW_PASSWORD`
4. Re-enter password if needed
5. Click **Save**

---

### **Error: "404 Not Found"**
**Cause:** Wrong instance URL or ticket doesn't exist

**Fix:**
1. Verify instance URL format: `https://devXXXXX.service-now.com` (no trailing slash)
2. Verify ticket numbers exist in ServiceNow
3. Check you're using the correct instance (dev vs prod)

---

### **Error: "Ticket not found"**
**Cause:** Ticket number doesn't exist in ServiceNow

**Fix:**
1. Go to ServiceNow portal
2. Create test incidents
3. Use the actual incident numbers from ServiceNow
4. Update the test payload with correct ticket numbers

---

### **Error: "Connection timeout"**
**Cause:** Network/firewall blocking Lambda to ServiceNow

**Fix:**
1. Check ServiceNow instance is publicly accessible
2. Verify no VPC restrictions on Lambda
3. Check ServiceNow IP whitelist (if configured)

---

### **Error: "Missing sys_id"**
**Cause:** Lambda can't find ticket in ServiceNow

**Fix:**
1. Verify ticket number format (e.g., INC0010001)
2. Check tickets exist in your ServiceNow instance
3. Try querying ServiceNow API directly to confirm ticket exists

---

## ✅ Verification Checklist

**Before Testing:**
- [ ] ServiceNow credentials added to Lambda
- [ ] Instance URL has no trailing slash
- [ ] Test tickets created in ServiceNow
- [ ] Lambda has internet access to reach ServiceNow

**Test Lambda Function:**
- [ ] Lambda test executed successfully
- [ ] Response shows "tickets_updated": 2
- [ ] No error messages in logs

**Check ServiceNow:**
- [ ] Open test tickets in ServiceNow portal
- [ ] Work notes appear with transfer details
- [ ] Ticket state changed to "Resolved"
- [ ] Timestamps are correct

**End-to-End Test:**
- [ ] demo.html loads successfully
- [ ] Transfer form submits without errors
- [ ] API Gateway receives request
- [ ] Step Functions execution completes
- [ ] ServiceNow tickets updated automatically

---

## 📊 Quick Test Commands

**PowerShell - Test ServiceNow API:**
```powershell
$cred = "username:password"
$base64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($cred))
Invoke-RestMethod -Uri "https://devXXXXX.service-now.com/api/now/table/incident?sysparm_limit=1" `
    -Headers @{Authorization = "Basic $base64"}
```

**AWS CLI - Test Lambda:**
```bash
aws lambda invoke \
  --function-name FileFerry-UpdateServiceNow \
  --payload '{"servicenow_tickets":["INC001"],"transfer_result":{"status":"completed"}}' \
  response.json
```

**Check Lambda Logs:**
```bash
aws logs tail /aws/lambda/FileFerry-UpdateServiceNow --follow
```

---

## 🎯 Next Steps

1. **Test Lambda function directly** (Method 1) - Takes 2 minutes
2. **Create real test tickets** in ServiceNow (Method 4) - Takes 5 minutes
3. **Run end-to-end test** with demo.html (Method 5) - Takes 10 minutes
4. **Verify tickets updated** in ServiceNow portal - Takes 2 minutes

**Total Time: ~20 minutes for complete verification** 🚀

---

**Ready to test? Start with Method 1 (Quick Lambda Test) in AWS Console!**
