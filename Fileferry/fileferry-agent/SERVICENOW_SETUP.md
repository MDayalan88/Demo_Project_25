# ServiceNow Integration Setup Guide

## 🎯 Overview

This guide will help you set up a **ServiceNow Personal Developer Instance** (free tier) and integrate it with the FileFerry agent to automatically create tickets for file transfer requests and audit trails.

---

## 📋 Step 1: Create ServiceNow Developer Instance (Free)

### 1.1 Register for ServiceNow Developer Account

1. **Visit:** https://developer.servicenow.com/
2. **Click:** "Sign Up and Start Building" or "Get Started"
3. **Fill out the registration form:**
   - First Name, Last Name
   - Email address
   - Password
   - Accept terms and conditions
4. **Click:** "Sign Up"
5. **Verify your email** (check inbox/spam)

### 1.2 Request Personal Developer Instance (PDI)

1. **Log in to:** https://developer.servicenow.com/
2. **Navigate to:** "Manage" → "Instance"
3. **Click:** "Request Instance"
4. **Select Release:** Choose the latest release (e.g., "Vancouver" or "Washington DC")
5. **Click:** "Request"
6. **Wait 2-5 minutes** for instance provisioning

### 1.3 Get Your Instance Details

Once provisioned, you'll receive:
- **Instance URL:** `https://devXXXXX.service-now.com` (where XXXXX is your instance ID)
- **Username:** `admin`
- **Password:** Click "Show Password" or check email

**Example:**
```
Instance URL: https://dev123456.service-now.com
Username: admin
Password: YourRandomPassword123!
```

---

## 🔧 Step 2: Configure ServiceNow Instance

### 2.1 Log in to Your Instance

1. Open your instance URL: `https://devXXXXX.service-now.com`
2. Log in with username `admin` and your password

### 2.2 Enable REST API Access

1. In ServiceNow, type **"System Web Services"** in the left navigation filter
2. Click **"REST" → "REST API Explorer"**
3. Verify you can access the API explorer (this confirms REST API is enabled)

### 2.3 Create API User (Recommended for Production)

For development, you can use the `admin` account, but for production:

1. Navigate to: **User Administration → Users**
2. Click **"New"**
3. Fill in:
   - **User ID:** `fileferry_api`
   - **First name:** FileFerry
   - **Last name:** API User
   - **Password:** Set a strong password
   - **Active:** ✅ Checked
4. Click **"Submit"**

5. **Assign Roles:**
   - Navigate to the user you just created
   - Scroll to **"Roles"** tab
   - Click **"Edit"**
   - Add roles: `itil`, `rest_service`
   - Click **"Save"**

### 2.4 Create Assignment Group

1. Navigate to: **User Administration → Groups**
2. Click **"New"**
3. Fill in:
   - **Name:** DataOps
   - **Description:** FileFerry Data Operations Team
   - **Type:** Leave as default
4. Click **"Submit"**
5. **Note the Group ID** (you'll see it in the URL after creation)

---

## 🔐 Step 3: Configure FileFerry Integration

### 3.1 Update Environment Variables

Create or update `.env` file in your project root:

```bash
# ServiceNow Configuration
SERVICENOW_INSTANCE_URL=https://devXXXXX.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=YourPassword123!
```

**For Windows PowerShell:**
```powershell
# Set environment variables
$env:SERVICENOW_INSTANCE_URL="https://devXXXXX.service-now.com"
$env:SERVICENOW_USERNAME="admin"
$env:SERVICENOW_PASSWORD="YourPassword123!"
```

### 3.2 Update config.yaml (Optional)

The config.yaml already has ServiceNow settings that use environment variables:

```yaml
servicenow:
  instance_url: ${SERVICENOW_INSTANCE_URL}
  username: ${SERVICENOW_USERNAME}
  password: ${SERVICENOW_PASSWORD}
  default_assignment_group: DataOps
  user_ticket_urgency: 2  # Medium
  audit_ticket_urgency: 3  # Low
```

---

## 🧪 Step 4: Test ServiceNow Integration

### 4.1 Test Connection Script

Run this PowerShell script to test your ServiceNow connection:

```powershell
# Test ServiceNow Connection

$instanceUrl = "https://devXXXXX.service-now.com"  # Replace with your instance
$username = "admin"
$password = "YourPassword123!"  # Replace with your password

# Create credentials
$pair = "$($username):$($password)"
$encodedCreds = [System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair))
$headers = @{
    Authorization = "Basic $encodedCreds"
    "Content-Type" = "application/json"
}

# Test: Get incident table
$uri = "$instanceUrl/api/now/table/incident?sysparm_limit=1"

try {
    $response = Invoke-RestMethod -Uri $uri -Method Get -Headers $headers
    Write-Host "✅ ServiceNow connection successful!" -ForegroundColor Green
    Write-Host "Response: $($response | ConvertTo-Json -Depth 2)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ ServiceNow connection failed!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}
```

### 4.2 Create Test Ticket

```powershell
# Create a test incident in ServiceNow

$instanceUrl = "https://devXXXXX.service-now.com"
$username = "admin"
$password = "YourPassword123!"

$pair = "$($username):$($password)"
$encodedCreds = [System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair))
$headers = @{
    Authorization = "Basic $encodedCreds"
    "Content-Type" = "application/json"
}

$body = @{
    short_description = "FileFerry Test - File Transfer Request"
    description = "Test ticket created from FileFerry agent integration"
    urgency = "2"
    impact = "2"
    assignment_group = "DataOps"
} | ConvertTo-Json

$uri = "$instanceUrl/api/now/table/incident"

try {
    $response = Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $body
    Write-Host "✅ Test ticket created successfully!" -ForegroundColor Green
    Write-Host "Ticket Number: $($response.result.number)" -ForegroundColor Cyan
    Write-Host "Ticket Sys ID: $($response.result.sys_id)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Failed to create ticket!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}
```

---

## 🚀 Step 5: Integrate with FileFerry Agent

### 5.1 Install Required Python Packages

```powershell
pip install aiohttp
```

### 5.2 Test Python Integration

Run the test script I'll create:

```powershell
python test_servicenow_integration.py
```

### 5.3 Enable ServiceNow in Agent

The FileFerry agent will automatically create tickets when:

1. **User requests a file transfer** → Creates user-facing incident ticket
2. **Transfer completes** → Updates ticket with results
3. **Transfer fails** → Updates ticket with error details
4. **Audit trail needed** → Creates separate audit ticket for compliance

---

## 📊 Step 6: Verify Integration

### 6.1 Check Tickets in ServiceNow

1. Log in to your ServiceNow instance
2. Navigate to: **Incident → All**
3. You should see tickets created by FileFerry with:
   - Short description containing "FileFerry"
   - Transfer details in description
   - Status updates

### 6.2 Test via API Endpoint

```powershell
# Test FileFerry API with ServiceNow integration
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

Invoke-RestMethod -Uri "http://localhost:8000/api/transfer/create" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

This should create a ticket in ServiceNow automatically!

---

## 🔍 Step 7: Monitor and Manage

### 7.1 View All FileFerry Tickets

1. In ServiceNow, go to **Incident → All**
2. Filter by: `Short description CONTAINS FileFerry`
3. Or create a saved filter for easy access

### 7.2 Ticket Workflow

**FileFerry creates two types of tickets:**

#### User Ticket (Medium Priority)
- **Purpose:** User-facing ticket for the requester
- **Short Description:** "FileFerry Transfer Request - [filename]"
- **Assignment Group:** DataOps
- **Updates:** Status changes (In Progress, Completed, Failed)

#### Audit Ticket (Low Priority)
- **Purpose:** Compliance and audit trail
- **Short Description:** "FileFerry Audit - [transfer_id]"
- **Contains:** Full transfer metadata, timestamps, user info
- **Immutable:** Created once for record-keeping

### 7.3 Custom Fields (Optional Enhancement)

Add custom fields to incident table:

1. Navigate to: **System Definition → Tables**
2. Find table: `incident`
3. Add columns:
   - `u_transfer_id` (String)
   - `u_source_file` (String)
   - `u_destination` (String)
   - `u_file_size` (Integer)
   - `u_transfer_status` (Choice: Pending, In Progress, Completed, Failed)

---

## 📚 ServiceNow API Reference

### Key Endpoints Used by FileFerry

```
POST /api/now/table/incident
GET  /api/now/table/incident/{sys_id}
PATCH /api/now/table/incident/{sys_id}
GET  /api/now/table/sys_user_group?sysparm_query=name=DataOps
```

### Response Format

```json
{
  "result": {
    "sys_id": "abc123...",
    "number": "INC0010001",
    "short_description": "FileFerry Transfer Request",
    "state": "1",
    "urgency": "2",
    "impact": "2"
  }
}
```

---

## 🐛 Troubleshooting

### Issue: "Invalid username or password"
**Solution:** 
- Verify credentials in ServiceNow Developer Portal
- Reset password if needed
- Check for special characters in password (may need URL encoding)

### Issue: "Assignment group not found"
**Solution:**
- Create the "DataOps" group in ServiceNow
- Or update `config.yaml` with an existing group name

### Issue: "403 Forbidden"
**Solution:**
- Ensure user has `itil` and `rest_service` roles
- Check instance is active (developer instances hibernate after inactivity)
- Wake up instance from developer portal

### Issue: "Instance not responding"
**Solution:**
- Developer instances hibernate after 10 days of inactivity
- Log in to developer.servicenow.com and wake up your instance
- Wait 2-3 minutes for instance to start

### Issue: "Connection timeout"
**Solution:**
- Check firewall/proxy settings
- Verify instance URL is correct
- Try accessing instance in browser first

---

## 🎓 Best Practices

1. **Use dedicated API user** (not admin) in production
2. **Store credentials securely** (use environment variables, not hardcoded)
3. **Implement rate limiting** (ServiceNow has API limits)
4. **Add retry logic** for transient failures
5. **Monitor ticket creation** to avoid duplicates
6. **Clean up test tickets** regularly
7. **Document custom fields** and workflows
8. **Set up notifications** for high-priority tickets

---

## 📞 Support Resources

- **ServiceNow Developer Portal:** https://developer.servicenow.com/
- **ServiceNow REST API Docs:** https://developer.servicenow.com/dev.do#!/reference/api/vancouver/rest/
- **ServiceNow Community:** https://community.servicenow.com/
- **FileFerry Docs:** See `docs/` folder in project

---

## ✅ Checklist

- [ ] Created ServiceNow developer account
- [ ] Requested and received PDI instance
- [ ] Logged in successfully
- [ ] Created DataOps assignment group
- [ ] Updated environment variables
- [ ] Tested connection with PowerShell script
- [ ] Created test ticket successfully
- [ ] Installed Python dependencies
- [ ] Ran integration test script
- [ ] Verified tickets appear in ServiceNow
- [ ] Tested via FileFerry API endpoint

---

## 🎉 Next Steps

Once ServiceNow is integrated:

1. **Customize ticket templates** for your organization
2. **Set up email notifications** for ticket updates
3. **Create dashboards** to track transfer metrics
4. **Implement SLA policies** for response times
5. **Add custom workflows** for approval processes
6. **Integrate with CMDB** for asset tracking

---

**Your ServiceNow instance is free for development and will remain active as long as you log in at least once every 10 days!**
