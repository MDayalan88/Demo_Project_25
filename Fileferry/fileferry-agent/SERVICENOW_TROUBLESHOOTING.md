# ServiceNow Troubleshooting Guide

## 🔍 Problem: ServiceNow Instance Not Working

If your ServiceNow instance at `https://devxxxxx.service-now.com` is not accessible, follow these steps:

---

## 🛏️ Issue 1: Instance Hibernation (Most Common)

**Symptom:** Page won't load, times out, or shows "instance not available"

**Cause:** ServiceNow Developer Instances hibernate after **10 days of inactivity**

### ✅ Solution:

1. **Log in to ServiceNow Developer Portal:**
   - Visit: https://developer.servicenow.com/
   - Click **"Sign In"**
   - Enter your credentials

2. **Wake Up Your Instance:**
   - Go to: **"Manage" → "Instance"**
   - You'll see your instance status
   - Click **"Wake Up"** or **"Start"** button
   - Wait **2-3 minutes** for instance to start

3. **Verify Instance is Active:**
   - Status should show **"Active"** or **"Running"**
   - Try accessing your instance URL again

---

## 🔑 Issue 2: Wrong Instance URL

**Symptom:** 404 error or page not found

### ✅ Solution:

1. **Check Your Actual Instance URL:**
   - Log in to https://developer.servicenow.com/
   - Go to **"Manage" → "Instance"**
   - Copy the **exact URL** shown (e.g., `https://dev123456.service-now.com`)

2. **Common Mistakes:**
   - ❌ `https://devxxxxx.service-now.com` (placeholder)
   - ✅ `https://dev123456.service-now.com` (actual instance)
   - Note: Your instance ID is a specific number, not "xxxxx"

---

## 🔐 Issue 3: Expired Instance

**Symptom:** Instance deleted or no longer available

**Cause:** Developer instances expire after extended inactivity (60+ days)

### ✅ Solution:

1. **Request New Instance:**
   - Go to: https://developer.servicenow.com/
   - Navigate: **"Manage" → "Instance"**
   - Click **"Request Instance"**
   - Select latest release
   - Wait 2-5 minutes for provisioning

2. **Update Your Credentials:**
   - Get new instance URL, username, password
   - Update `.env` file or run `setup-servicenow.ps1`

---

## 🌐 Issue 4: Network/Firewall Issues

**Symptom:** Connection timeout or refused

### ✅ Solution:

1. **Check Your Internet Connection:**
   ```powershell
   Test-NetConnection -ComputerName "developer.servicenow.com" -Port 443
   ```

2. **Test Direct Access:**
   ```powershell
   Invoke-WebRequest -Uri "https://developer.servicenow.com" -UseBasicParsing
   ```

3. **Check Proxy Settings:**
   - If behind corporate firewall, configure proxy
   - Or use VPN if required

---

## 🧪 Quick Diagnostic Tests

### Test 1: Check Instance Availability

```powershell
# Replace devXXXXXX with your actual instance ID
$instanceUrl = "https://devXXXXXX.service-now.com"

try {
    $response = Invoke-WebRequest -Uri $instanceUrl -TimeoutSec 10 -UseBasicParsing
    Write-Host "✅ Instance is accessible!" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Instance not accessible" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Possible reasons:" -ForegroundColor Yellow
    Write-Host "  1. Instance is hibernated (wake it up on developer portal)"
    Write-Host "  2. Wrong instance URL (check developer portal for correct URL)"
    Write-Host "  3. Instance expired (request new instance)"
}
```

### Test 2: Verify Credentials

```powershell
$instanceUrl = "https://devXXXXXX.service-now.com"
$username = "admin"
$password = "YourPassword123!"

$pair = "$($username):$($password)"
$encodedCreds = [System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair))
$headers = @{
    Authorization = "Basic $encodedCreds"
    "Content-Type" = "application/json"
}

try {
    $response = Invoke-RestMethod -Uri "$instanceUrl/api/now/table/incident?sysparm_limit=1" -Method Get -Headers $headers
    Write-Host "✅ Credentials are valid!" -ForegroundColor Green
} catch {
    Write-Host "❌ Authentication failed" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
}
```

---

## 📝 Step-by-Step: Wake Up Hibernated Instance

1. **Open Browser:** https://developer.servicenow.com/

2. **Sign In:**
   - Use your ServiceNow developer account credentials

3. **Navigate to Instance Management:**
   - Top menu: Click **"Manage"**
   - Dropdown: Select **"Instance"**

4. **Check Instance Status:**
   - You'll see your instance listed
   - Look for status indicator
   - **"Hibernating"** or **"Stopped"** = needs to be woken up

5. **Wake Up Instance:**
   - Click **"Wake Up"** or **"Start"** button
   - Wait message appears: "Waking up instance..."
   - Wait **2-3 minutes**

6. **Verify Active Status:**
   - Status changes to **"Active"** or **"Running"**
   - Instance URL becomes clickable
   - Click URL to test access

7. **Test Login:**
   - Click your instance URL
   - Log in with username: `admin`
   - Password: (shown in developer portal or previously saved)

---

## 🔄 Get Your Instance Details

Run this to find your correct instance URL:

1. **Log in to Developer Portal:**
   https://developer.servicenow.com/

2. **Navigate to:**
   Manage → Instance

3. **Copy These Details:**
   - **Instance URL:** `https://devXXXXXX.service-now.com`
   - **Instance ID:** (the numbers in URL)
   - **Username:** `admin`
   - **Password:** Click "Show Password" or reset if forgotten

4. **Update FileFerry Configuration:**

   **Option A: Use Setup Script**
   ```powershell
   .\setup-servicenow.ps1
   ```
   Enter your actual instance URL when prompted

   **Option B: Manual Update**
   ```powershell
   $env:SERVICENOW_INSTANCE_URL="https://devXXXXXX.service-now.com"
   $env:SERVICENOW_USERNAME="admin"
   $env:SERVICENOW_PASSWORD="YourActualPassword"
   ```

---

## ⚡ Quick Fix Commands

### Wake Up and Test (PowerShell)

```powershell
# Step 1: Manually wake up instance on developer portal first!
# Then run this test:

$instanceUrl = "https://devXXXXXX.service-now.com"  # ← Replace with YOUR instance

Write-Host "Testing ServiceNow instance: $instanceUrl" -ForegroundColor Cyan

# Test basic connectivity
try {
    $response = Invoke-WebRequest -Uri $instanceUrl -TimeoutSec 15 -UseBasicParsing
    Write-Host "✅ Instance is UP and accessible!" -ForegroundColor Green
    
    # Now test with credentials
    $username = Read-Host "Enter username (default: admin)"
    if (-not $username) { $username = "admin" }
    $securePassword = Read-Host "Enter password" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
    $password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    
    $pair = "$($username):$($password)"
    $encodedCreds = [System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair))
    $headers = @{ Authorization = "Basic $encodedCreds" }
    
    $apiResponse = Invoke-RestMethod -Uri "$instanceUrl/api/now/table/incident?sysparm_limit=1" -Method Get -Headers $headers
    Write-Host "✅ API access successful!" -ForegroundColor Green
    Write-Host "✅ Credentials are valid!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Go to https://developer.servicenow.com/" -ForegroundColor Gray
    Write-Host "2. Sign in to your account" -ForegroundColor Gray
    Write-Host "3. Navigate to: Manage → Instance" -ForegroundColor Gray
    Write-Host "4. Click 'Wake Up' button" -ForegroundColor Gray
    Write-Host "5. Wait 2-3 minutes and try again" -ForegroundColor Gray
}
```

---

## 📚 Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| **Connection timeout** | Instance hibernated or down | Wake up on developer portal |
| **404 Not Found** | Wrong URL | Check instance URL on portal |
| **401 Unauthorized** | Wrong credentials | Reset password on portal |
| **Instance not available** | Expired or deleted | Request new instance |
| **ERR_NAME_NOT_RESOLVED** | Invalid instance ID | Verify correct instance URL |

---

## 🎯 Final Checklist

- [ ] Logged in to https://developer.servicenow.com/
- [ ] Navigated to Manage → Instance
- [ ] Instance status shows "Active" or "Running"
- [ ] Copied correct instance URL (not devxxxxx)
- [ ] Tested instance URL in browser
- [ ] Can log in with admin credentials
- [ ] Updated FileFerry `.env` or environment variables
- [ ] Restarted FileFerry backend
- [ ] Ran test: `python test_servicenow_integration.py`

---

## 💡 Pro Tips

1. **Keep Instance Active:**
   - Log in at least once every 10 days
   - Set a calendar reminder

2. **Save Credentials:**
   - Store in password manager
   - Or keep `.env` file backed up

3. **Test Regularly:**
   - Run weekly: `python test_servicenow_integration.py`

4. **Monitor Status:**
   - Check developer portal dashboard
   - Enable email notifications

---

## 🆘 Still Not Working?

1. **Request New Instance:**
   - Sometimes easier than troubleshooting old one
   - Takes only 2-5 minutes
   - Free with developer account

2. **Contact ServiceNow Support:**
   - Community: https://community.servicenow.com/
   - Developer Forum: https://developer.servicenow.com/connect.do

3. **Check ServiceNow Status:**
   - https://status.servicenow.com/
   - Verify no platform-wide outages

---

**Next Step: Go to https://developer.servicenow.com/ and wake up your instance!** 🚀
