# 🎫 ServiceNow Integration - Quick Start

## Overview

FileFerry agent automatically creates ServiceNow tickets for all file transfer requests, providing complete audit trail and tracking capabilities.

---

## ⚡ Quick Setup (5 Minutes)

### Step 1: Get ServiceNow Free Instance

1. Visit: **https://developer.servicenow.com/**
2. Click **"Sign Up"** and create account
3. Request a **Personal Developer Instance (PDI)**
4. Wait 2-5 minutes for provisioning
5. Note your credentials:
   - **Instance URL**: `https://devXXXXX.service-now.com`
   - **Username**: `admin`
   - **Password**: (shown on portal)

### Step 2: Configure FileFerry

Run the setup script:

```powershell
.\setup-servicenow.ps1
```

This will:
- Prompt for your ServiceNow credentials
- Save them to `.env` file
- Test the connection
- Set environment variables

### Step 3: Test Integration

```powershell
python test_servicenow_integration.py
```

This will create a test ticket and verify everything works.

### Step 4: Restart Backend

```powershell
python src\slack_bot\slack_api_simple.py
```

You should see:
```
✅ ServiceNow integration ENABLED
   Instance: https://devXXXXX.service-now.com
```

---

## 🎯 What It Does

When you create a file transfer via FileFerry:

1. **User Ticket Created** → Incident with Medium priority
2. **Transfer Details** → All metadata logged
3. **Status Updates** → Ticket updated as transfer progresses
4. **Completion** → Ticket closed with results

**Example Ticket:**
```
Ticket Number: INC0010001
Short Description: FileFerry Transfer - data_export.csv
Description:
  Source: my-bucket/data_export.csv
  Destination: ftp://ftp.example.com/uploads/
  User: user@example.com
  Status: completed
  Timestamp: 2025-12-03T10:30:00Z
```

---

## 📖 Documentation

- **Full Setup Guide**: `SERVICENOW_SETUP.md` (detailed instructions)
- **Test Script**: `test_servicenow_integration.py` (comprehensive testing)
- **Setup Script**: `setup-servicenow.ps1` (automated configuration)

---

## 🔧 Manual Configuration

If you prefer manual setup:

### 1. Set Environment Variables

**Windows PowerShell:**
```powershell
$env:SERVICENOW_INSTANCE_URL="https://devXXXXX.service-now.com"
$env:SERVICENOW_USERNAME="admin"
$env:SERVICENOW_PASSWORD="YourPassword123!"
```

**Or create `.env` file:**
```bash
SERVICENOW_INSTANCE_URL=https://devXXXXX.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=YourPassword123!
```

### 2. Create DataOps Group (in ServiceNow)

1. Log in to ServiceNow
2. Navigate: **User Administration → Groups**
3. Click **"New"**
4. Name: `DataOps`
5. Click **"Submit"**

### 3. Test Connection

```powershell
$instanceUrl = "https://devXXXXX.service-now.com"
$username = "admin"
$password = "YourPassword123!"

$pair = "$($username):$($password)"
$encodedCreds = [System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair))
$headers = @{
    Authorization = "Basic $encodedCreds"
    "Content-Type" = "application/json"
}

Invoke-RestMethod -Uri "$instanceUrl/api/now/table/incident?sysparm_limit=1" -Method Get -Headers $headers
```

---

## 🧪 Testing

### Test via Python Script

```powershell
python test_servicenow_integration.py
```

**What it tests:**
- ✅ Connection to ServiceNow
- ✅ Assignment group exists
- ✅ Create ticket
- ✅ Update ticket
- ✅ Close ticket

### Test via API

Create a transfer to automatically generate a ticket:

```powershell
$body = @{
    user_id = "test_user"
    source_bucket = "my-bucket"
    source_key = "test-file.csv"
    destination_type = "ftp"
    destination_host = "ftp.example.com"
    destination_path = "/upload/"
    destination_user = "ftpuser"
    destination_password = "pass123"
    priority = "high"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/transfer/create" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"

# Check the response for ServiceNow ticket number
$response.servicenow_ticket
```

### View Tickets in ServiceNow

1. Open: `https://devXXXXX.service-now.com`
2. Navigate: **Incident → All**
3. Filter by: `Short description CONTAINS FileFerry`

---

## 🎨 Ticket Details

### User Ticket
- **Type**: Incident
- **Priority**: Medium (2)
- **Impact**: Medium (2)
- **Assignment Group**: DataOps
- **Short Description**: FileFerry Transfer - [filename]
- **Description**: Complete transfer details

### Information Included
- Transfer ID
- Source bucket and key
- Destination type and host
- File size
- User ID
- Priority level
- Status
- Timestamps

---

## 🔍 Monitoring

### Check Backend Logs

When ServiceNow is enabled, you'll see:

```
✅ ServiceNow integration ENABLED
   Instance: https://devXXXXX.service-now.com
🚀 Creating transfer for user: test_user
✅ ServiceNow ticket created: INC0010001
```

### API Health Check

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get
```

Response includes:
```json
{
  "status": "healthy",
  "servicenow_enabled": true
}
```

---

## 🐛 Troubleshooting

### "ServiceNow disabled" message

**Cause**: Credentials not found in environment
**Fix**: Run `.\setup-servicenow.ps1` or set environment variables

### "Connection failed" error

**Possible causes:**
1. **Wrong credentials** → Verify on developer.servicenow.com
2. **Instance hibernated** → Log in to portal and wake up instance
3. **Wrong URL** → Check format: `https://devXXXXX.service-now.com`

### "Assignment group not found"

**Fix**: Create "DataOps" group in ServiceNow:
1. User Administration → Groups
2. Click "New"
3. Name: DataOps
4. Submit

### Tickets not appearing

1. Check backend logs for errors
2. Verify credentials in `.env`
3. Run test script: `python test_servicenow_integration.py`
4. Check ServiceNow instance is active

---

## 📚 Additional Resources

- **ServiceNow Developer Portal**: https://developer.servicenow.com/
- **REST API Docs**: https://developer.servicenow.com/dev.do#!/reference/api/vancouver/rest/
- **Full Setup Guide**: See `SERVICENOW_SETUP.md`

---

## ✅ Verification Checklist

- [ ] Created ServiceNow developer account
- [ ] Received PDI instance
- [ ] Ran `setup-servicenow.ps1`
- [ ] Connection test passed
- [ ] Ran `test_servicenow_integration.py`
- [ ] Test ticket created successfully
- [ ] Restarted backend API
- [ ] Saw "ServiceNow integration ENABLED" message
- [ ] Created test transfer
- [ ] Verified ticket in ServiceNow portal

---

**🎉 You're all set! Every file transfer will now automatically create a ServiceNow ticket.**
