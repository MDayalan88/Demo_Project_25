# Setup ServiceNow Integration Script
# This script helps you configure ServiceNow credentials for FileFerry

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "    FileFerry - ServiceNow Integration Setup            " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

# Your ServiceNow Instance
$instanceUrl = "https://dev329630.service-now.com"

Write-Host "Your ServiceNow Instance: " -NoNewline
Write-Host $instanceUrl -ForegroundColor Green
Write-Host ""

# Check if .env file exists
$envFile = ".env"

if (Test-Path $envFile) {
    Write-Host "[OK] .env file found" -ForegroundColor Green
} else {
    Write-Host "[INFO] Creating new .env file..." -ForegroundColor Yellow
}

# Prompt for credentials
Write-Host ""
Write-Host "Please enter your ServiceNow credentials:" -ForegroundColor Yellow
Write-Host "(Default username for developer instance is 'admin')" -ForegroundColor Gray
Write-Host ""

$username = Read-Host "Username (press Enter for 'admin')"
if ([string]::IsNullOrWhiteSpace($username)) {
    $username = "admin"
}

$password = Read-Host "Password" -AsSecureString
$passwordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))

if ([string]::IsNullOrWhiteSpace($passwordPlain)) {
    Write-Host ""
    Write-Host "❌ Password cannot be empty!" -ForegroundColor Red
    Write-Host "Please run this script again and enter your password." -ForegroundColor Yellow
    exit 1
}

# Create/Update .env file
$envContent = @"
# ServiceNow Configuration
SERVICENOW_INSTANCE_URL=$instanceUrl
SERVICENOW_USERNAME=$username
SERVICENOW_PASSWORD=$passwordPlain

# Instructions:
# This file is git-ignored for security
# If you change credentials, restart the backend: python .\src\slack_bot\slack_api_simple.py
"@

$envContent | Out-File -FilePath $envFile -Encoding UTF8
Write-Host ""
Write-Host "[OK] Configuration saved to .env file" -ForegroundColor Green

# Set environment variables for current session
$env:SERVICENOW_INSTANCE_URL = $instanceUrl
$env:SERVICENOW_USERNAME = $username
$env:SERVICENOW_PASSWORD = $passwordPlain

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "    Testing ServiceNow Connection                       " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

# Test connection using PowerShell
Write-Host "Testing connection..." -ForegroundColor Yellow
Write-Host ""

try {
    $base64Auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${username}:${passwordPlain}"))
    $headers = @{
        "Authorization" = "Basic $base64Auth"
        "Accept" = "application/json"
    }
    
    $testUrl = "$instanceUrl/api/now/table/incident?sysparm_limit=1"
    Write-Host "Testing: $testUrl" -ForegroundColor Gray
    
    $response = Invoke-RestMethod -Uri $testUrl -Method Get -Headers $headers -TimeoutSec 15
    
    Write-Host ""
    Write-Host "[SUCCESS] Connection successful!" -ForegroundColor Green
    Write-Host "Your ServiceNow instance is accessible and credentials are valid." -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "[ERROR] Connection failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  1. Instance is hibernated - Visit https://developer.servicenow.com/ to wake it up" -ForegroundColor Gray
    Write-Host "  2. Wrong password - Check your credentials" -ForegroundColor Gray
    Write-Host "  3. Network issues - Check your internet connection" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "    Next Steps                                          " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Create 'DataOps' assignment group in ServiceNow:" -ForegroundColor Yellow
Write-Host "   - Go to: User Administration -> Groups" -ForegroundColor Gray
Write-Host "   - Click 'New'" -ForegroundColor Gray
Write-Host "   - Name: DataOps" -ForegroundColor Gray
Write-Host "   - Add yourself as a member" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Start the backend API:" -ForegroundColor Yellow
Write-Host "   python .\src\slack_bot\slack_api_simple.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start the frontend (after installing Node.js):" -ForegroundColor Yellow
Write-Host "   cd frontend" -ForegroundColor Gray
Write-Host "   npm install" -ForegroundColor Gray
Write-Host "   npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "[DONE] Setup complete! ServiceNow integration is ready." -ForegroundColor Green
Write-Host ""
