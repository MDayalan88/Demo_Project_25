# FileFerry End-to-End Demo Guide

## 🎯 Demo Overview

This guide will walk you through a complete FileFerry demonstration showing:
1. **Modern Web UI** - Login, Dashboard, File Transfer Request
2. **Backend API** - FastAPI server handling requests
3. **ServiceNow Integration** - Automatic ticket creation
4. **AI Agent** - Bedrock AI for intelligent file transfers

---

## 📋 Prerequisites Checklist

### ✅ What You Have:
- [x] Python installed
- [x] FastAPI and Uvicorn installed
- [x] ServiceNow instance configured: https://dev329630.service-now.com
- [x] Modern UI code complete (5 pages)
- [x] Backend API ready
- [x] Demo HTML file (no Node.js needed)

### ⚠️ What's Missing:
- [ ] Node.js (not required - use demo.html instead)
- [ ] AWS credentials (optional for full demo)

---

## 🚀 Quick Demo (5 Minutes) - UI Only

### Step 1: Open Demo HTML
```powershell
# Open the standalone demo in browser
Start-Process "C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend\demo.html"
```

### Step 2: Test the Flow
1. **Login**: Use any username/password → Click "Sign In"
2. **Dashboard**: Click "FileFerry" card
3. **File Transfer Form**:
   - Assignment Group: Select "DataOps Team"
   - Environment: Choose "PROD"
   - Bucket Name: Enter "my-production-bucket"
   - File Name: Enter "data_export_2025.csv"
   - Priority: Select "High"
   - Click "Continue to AWS SSO"
4. **AWS SSO**: See success confirmation → Click "Return to Dashboard"
5. **Change Request**: Click "Change Request" card → Fill form

**Duration: 3-5 minutes**

---

## 🔧 Full Demo (15 Minutes) - UI + Backend

### Step 1: Start Backend API

**Terminal 1 - Backend API:**
```powershell
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent

# Start the FastAPI backend
python src\slack_bot\slack_api.py
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**API Endpoints Available:**
- `http://localhost:8000/` - Health check
- `http://localhost:8000/api/transfer/create` - Create transfer
- `http://localhost:8000/api/transfer/history` - Get history
- `http://localhost:8000/api/s3/buckets` - List buckets
- `http://localhost:8000/api/chat` - AI chat
- `http://localhost:8000/servicenow/test` - Test ServiceNow

### Step 2: Test ServiceNow Integration

**Terminal 2 - Test ServiceNow:**
```powershell
# Check ServiceNow configuration
$env:SERVICENOW_INSTANCE_URL
$env:SERVICENOW_USERNAME

# Test ServiceNow connection (open browser)
Start-Process "http://localhost:8000/servicenow/test"
```

**Expected Result:**
```json
{
  "status": "success",
  "ticket_number": "INC0010XXX",
  "message": "ServiceNow integration working"
}
```

### Step 3: Open Modern UI Demo

**Browser:**
```powershell
Start-Process "C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend\demo.html"
```

### Step 4: Test Backend API Calls

**Terminal 3 - Test API:**
```powershell
# Test health check
Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get

# Test transfer creation
$body = @{
    source_type = "s3"
    source_bucket = "my-bucket"
    source_key = "data.csv"
    dest_type = "ftp"
    dest_host = "ftp.example.com"
    dest_path = "/uploads"
    priority = "high"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/transfer/create" -Method Post -Body $body -ContentType "application/json"
```

**Expected Output:**
```json
{
  "request_id": "REQ-1733241600",
  "status": "pending",
  "servicenow_ticket": "INC0010XXX"
}
```

---

## 🎬 Complete End-to-End Demo Script

### Scenario: Transfer Production Data File

**Story:**
"I need to transfer a critical data export file from S3 to our partner's FTP server with high priority."

### Demo Flow (10 minutes):

#### 1. **Open UI and Login** (30 seconds)
```
Action: Open demo.html in browser
Login: Username: "demo-user", Password: "demo123"
Result: Redirected to Dashboard
```

#### 2. **View Dashboard** (30 seconds)
```
Action: Review dashboard statistics
Show: Active Transfers: 12, Success Rate: 98.5%, Pending: 3
Point out: Two main options - FileFerry and Change Request
```

#### 3. **Create File Transfer Request** (2 minutes)
```
Action: Click "FileFerry" card
Fill Form:
  - Assignment Group: DataOps Team
  - Environment: PROD (red badge)
  - Bucket Name: production-data-exports
  - File Name: customer_export_dec2025.csv
  - Priority: High (immediate processing)
Show: Form validation - submit disabled until all fields filled
Action: Click "Continue to AWS SSO"
```

#### 4. **AWS SSO Authentication** (1 minute)
```
Show: Request summary displayed
Show: Security features (MFA, Encryption, Session Mgmt, Audit)
Action: Click "Authenticate with AWS SSO"
Show: Loading animation with 3 steps
Result: Success screen with Request ID (FT-1733241600)
Wait: Auto-redirect to dashboard after 2 seconds
```

#### 5. **Test Backend API** (2 minutes)
```powershell
# In terminal - show API call
Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get

# Show transfer history
Invoke-RestMethod -Uri "http://localhost:8000/api/transfer/history" -Method Get
```

#### 6. **Verify ServiceNow Ticket** (2 minutes)
```
Action: Open browser to http://localhost:8000/servicenow/test
Result: Shows ticket created with number INC0010XXX
Alternative: Open ServiceNow instance directly
URL: https://dev329630.service-now.com
Navigate to: Incident → Open
Find: Latest ticket created by API
```

#### 7. **Test Change Request Flow** (2 minutes)
```
Action: Return to dashboard → Click "Change Request" card
Fill Form:
  - Title: "Deploy new file transfer automation"
  - Type: Standard Change
  - Priority: High
  - Target Date: Next week
  - Assign To: Infrastructure Team
  - Description: "Implement automated file transfer workflow"
Action: Click "Submit Request"
Result: Return to dashboard with success
```

#### 8. **Show Legacy UI (Bonus)** (1 minute)
```
Explain: Application has backward compatibility
Show: Original UI still available with header navigation
Note: New modern UI is the recommended interface
```

---

## 📊 Demo Talking Points

### Modern UI Features:
✅ **Security**: Protected routes with authentication
✅ **Validation**: Real-time form validation
✅ **UX**: Smooth animations and hover effects
✅ **Responsive**: Works on mobile and desktop
✅ **Accessibility**: Color-coded priorities, breadcrumbs
✅ **Professional**: Purple-indigo gradient branding

### Backend Capabilities:
✅ **FastAPI**: High-performance async API
✅ **ServiceNow**: Automatic ticket creation
✅ **AWS Integration**: S3, Bedrock AI, SSO
✅ **DynamoDB**: State persistence
✅ **Multi-protocol**: S3, FTP, SFTP support

### Business Value:
✅ **Automation**: Reduces manual file transfers
✅ **Auditability**: ServiceNow ticket for every transfer
✅ **Priority Management**: SLA-based processing
✅ **Security**: AWS SSO, encrypted connections
✅ **AI-Powered**: Intelligent error handling

---

## 🎥 Demo Screenshots Guide

### What to Show in Each Screen:

**1. Login Page:**
- Point out: FileFerry logo, gradient background
- Mention: Demo mode (any credentials work)
- Show: Loading state when clicking "Sign In"

**2. Dashboard:**
- Highlight: Welcome message with username
- Point out: Two main action cards
- Show: Statistics section (active transfers, success rate)
- Demonstrate: Hover effects on cards

**3. File Transfer Form:**
- Show: Breadcrumb navigation
- Point out: All 5 required fields
- Demonstrate: Radio button selection for environment
- Show: Color-coded priorities (High=red, Medium=orange, Low=green)
- Explain: Submit disabled until form valid

**4. AWS SSO Page:**
- Show: Request summary from previous form
- Point out: Security features grid
- Demonstrate: Authentication flow animation
- Show: Success with generated Request ID

**5. Change Request Form:**
- Show: Different color scheme (blue vs purple)
- Point out: Date picker with future dates only
- Show: Character counter on description
- Demonstrate: Form submission flow

---

## 🐛 Troubleshooting Demo Issues

### Issue: Backend won't start
```powershell
# Check if port 8000 is in use
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

# Kill process if needed
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force

# Try different port
$env:PORT = "8001"
python src\slack_bot\slack_api.py
```

### Issue: ServiceNow test fails
```powershell
# Verify environment variables
Write-Host "Instance URL: $env:SERVICENOW_INSTANCE_URL"
Write-Host "Username: $env:SERVICENOW_USERNAME"
Write-Host "Password: $(if($env:SERVICENOW_PASSWORD){'***SET***'}else{'NOT SET'})"

# Re-set if needed
$env:SERVICENOW_INSTANCE_URL = "https://dev329630.service-now.com"
$env:SERVICENOW_USERNAME = "admin"
$env:SERVICENOW_PASSWORD = "your-password"
```

### Issue: Demo HTML not loading properly
```powershell
# Try opening in different browser
Start-Process chrome "C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend\demo.html"
Start-Process msedge "C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend\demo.html"

# Or open manually and check console (F12)
```

---

## 📝 Demo Checklist

### Before Demo:
- [ ] Backend API server started (Terminal 1)
- [ ] ServiceNow credentials set in environment
- [ ] Demo HTML file ready to open
- [ ] Browser windows organized
- [ ] Terminal windows visible for live API calls

### During Demo:
- [ ] Start with login page
- [ ] Show dashboard navigation
- [ ] Complete full file transfer flow
- [ ] Demonstrate form validation
- [ ] Show ServiceNow integration
- [ ] Test change request flow
- [ ] Show backend API calls in terminal
- [ ] Verify ServiceNow ticket creation

### Demo Success Criteria:
- [ ] Login flow works smoothly
- [ ] All form validations visible
- [ ] AWS SSO flow completes
- [ ] Request ID generated
- [ ] API responds correctly
- [ ] ServiceNow ticket created (if backend running)

---

## 🎯 Quick Start Commands

**Copy and paste these to get started quickly:**

```powershell
# Navigate to project
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent

# Option 1: Just UI Demo (No backend needed)
Start-Process "C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend\demo.html"

# Option 2: Full Demo with Backend
# Terminal 1 - Start backend
python src\slack_bot\slack_api.py

# Terminal 2 - Open UI
Start-Process "C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend\demo.html"

# Terminal 3 - Test API
Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get
```

---

## 🎉 Demo Summary

**What the audience will see:**
1. Modern, professional web application
2. Secure login with authentication
3. Intuitive dashboard navigation
4. Comprehensive form validation
5. Multi-step AWS SSO authentication
6. Automatic ServiceNow ticket creation
7. RESTful API backend
8. Real-time status updates

**Total Demo Time:**
- Quick UI-only demo: **5 minutes**
- Full demo with backend: **15 minutes**
- Deep dive with Q&A: **30 minutes**

---

## 📚 Additional Resources

- **UI Documentation**: `MODERN_UI_GUIDE.md`
- **Backend API**: `src/slack_bot/slack_api.py`
- **ServiceNow Setup**: `SERVICENOW_SETUP.md`
- **Architecture**: `docs/ARCHITECTURE.md`

---

**🚀 Ready to demo! Start with the Quick Demo (UI Only) to get familiar, then progress to Full Demo when ready.**
