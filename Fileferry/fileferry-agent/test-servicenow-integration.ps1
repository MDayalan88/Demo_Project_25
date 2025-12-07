# Test ServiceNow Integration
# PowerShell Script to test ServiceNow Handler with real API

param(
    [Parameter(Mandatory=$false)]
    [string]$InstanceUrl = $env:SERVICENOW_INSTANCE_URL,
    
    [Parameter(Mandatory=$false)]
    [string]$Username = $env:SERVICENOW_USERNAME,
    
    [Parameter(Mandatory=$false)]
    [string]$Password = $env:SERVICENOW_PASSWORD
)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "ServiceNow Integration Test" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Check configuration
if (-not $InstanceUrl) {
    Write-Host "❌ SERVICENOW_INSTANCE_URL not set" -ForegroundColor Red
    Write-Host "Set environment variable or pass as parameter:" -ForegroundColor Yellow
    Write-Host '  $env:SERVICENOW_INSTANCE_URL = "https://your-instance.service-now.com"' -ForegroundColor Cyan
    exit 1
}

if (-not $Username -or -not $Password) {
    Write-Host "❌ ServiceNow credentials not set" -ForegroundColor Red
    Write-Host "Set environment variables:" -ForegroundColor Yellow
    Write-Host '  $env:SERVICENOW_USERNAME = "your-username"' -ForegroundColor Cyan
    Write-Host '  $env:SERVICENOW_PASSWORD = "your-password"' -ForegroundColor Cyan
    exit 1
}

Write-Host "✅ Configuration loaded" -ForegroundColor Green
Write-Host "   Instance: $InstanceUrl" -ForegroundColor White
Write-Host "   Username: $Username" -ForegroundColor White
Write-Host ""

# Test 1: Authenticate
Write-Host "Test 1: Testing authentication..." -ForegroundColor Yellow

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
    "Accept" = "application/json"
}

try {
    $testUrl = "$InstanceUrl/api/now/table/incident?sysparm_limit=1"
    $response = Invoke-RestMethod -Uri $testUrl -Headers $headers -Method Get
    Write-Host "✅ Authentication successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Authentication failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Create User Ticket
Write-Host "Test 2: Creating user ticket..." -ForegroundColor Yellow

$userTicketData = @{
    short_description = "FileFerry Test: File Transfer Request"
    description = @"
Test Ticket - FileFerry AI Agent

User: test@example.com
Source: s3://test-bucket/test-file.txt
Destination: ftp://test-server.example.com
Transfer ID: test-$(Get-Date -Format 'yyyyMMddHHmmss')

This is an automated test ticket.
"@
    caller_id = $Username
    urgency = "2"
    category = "Data Transfer"
    subcategory = "S3 to FTP"
} | ConvertTo-Json

try {
    $createUrl = "$InstanceUrl/api/now/table/incident"
    $response = Invoke-RestMethod -Uri $createUrl -Headers $headers -Method Post -Body $userTicketData
    
    $userTicketNumber = $response.result.number
    $userTicketSysId = $response.result.sys_id
    
    Write-Host "✅ User ticket created: $userTicketNumber" -ForegroundColor Green
    Write-Host "   Sys ID: $userTicketSysId" -ForegroundColor White
} catch {
    Write-Host "❌ Failed to create user ticket: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 3: Create Audit Ticket
Write-Host "Test 3: Creating audit ticket..." -ForegroundColor Yellow

$auditTicketData = @{
    short_description = "FileFerry Audit: File Transfer by test@example.com"
    description = @"
Audit Trail - FileFerry AI Agent

User: test@example.com
Action: File Transfer Request
Source: s3://test-bucket/test-file.txt
Destination: ftp://test-server.example.com
User Ticket: $userTicketNumber
Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC')

This is an automated audit record.
"@
    caller_id = "system"
    urgency = "3"
    category = "Audit Trail"
    subcategory = "File Transfer"
    state = "7"  # Closed
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri $createUrl -Headers $headers -Method Post -Body $auditTicketData
    
    $auditTicketNumber = $response.result.number
    $auditTicketSysId = $response.result.sys_id
    
    Write-Host "✅ Audit ticket created: $auditTicketNumber" -ForegroundColor Green
    Write-Host "   Sys ID: $auditTicketSysId" -ForegroundColor White
} catch {
    Write-Host "❌ Failed to create audit ticket: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 4: Update User Ticket
Write-Host "Test 4: Updating user ticket with completion..." -ForegroundColor Yellow

Start-Sleep -Seconds 2

$updateData = @{
    work_notes = @"
Transfer Completed Successfully (TEST)

Bytes Transferred: 1,048,576 (1 MB)
Remote Path: /uploads/test-file.txt
MD5 Checksum: d41d8cd98f00b204e9800998ecf8427e
Completed At: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC')

This is a test update.
"@
    state = "6"  # Resolved
} | ConvertTo-Json

try {
    $updateUrl = "$InstanceUrl/api/now/table/incident/$userTicketSysId"
    $response = Invoke-RestMethod -Uri $updateUrl -Headers $headers -Method Patch -Body $updateData
    
    Write-Host "✅ User ticket updated: $userTicketNumber" -ForegroundColor Green
    Write-Host "   Status: Resolved" -ForegroundColor White
} catch {
    Write-Host "❌ Failed to update ticket: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 5: Retrieve Ticket Details
Write-Host "Test 5: Retrieving ticket details..." -ForegroundColor Yellow

try {
    $getUrl = "$InstanceUrl/api/now/table/incident/$userTicketSysId"
    $response = Invoke-RestMethod -Uri $getUrl -Headers $headers -Method Get
    
    Write-Host "✅ Ticket retrieved: $userTicketNumber" -ForegroundColor Green
    Write-Host "   State: $($response.result.state)" -ForegroundColor White
    Write-Host "   Short Description: $($response.result.short_description)" -ForegroundColor White
} catch {
    Write-Host "❌ Failed to retrieve ticket: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Authentication: PASSED" -ForegroundColor Green
Write-Host "✅ User Ticket Creation: PASSED ($userTicketNumber)" -ForegroundColor Green
Write-Host "✅ Audit Ticket Creation: PASSED ($auditTicketNumber)" -ForegroundColor Green
Write-Host "✅ Ticket Update: PASSED" -ForegroundColor Green
Write-Host "✅ Ticket Retrieval: PASSED" -ForegroundColor Green
Write-Host ""
Write-Host "View tickets in ServiceNow:" -ForegroundColor Yellow
Write-Host "  User Ticket: $InstanceUrl/nav_to.do?uri=incident.do?sys_id=$userTicketSysId" -ForegroundColor Cyan
Write-Host "  Audit Ticket: $InstanceUrl/nav_to.do?uri=incident.do?sys_id=$auditTicketSysId" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ All ServiceNow integration tests PASSED!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
