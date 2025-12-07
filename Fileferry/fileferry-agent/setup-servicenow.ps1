# ServiceNow Setup Script for FileFerry
# This script helps you configure ServiceNow credentials

Write-Host "🎫 FileFerry ServiceNow Configuration" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
$envFile = Join-Path $PSScriptRoot ".env"
$envExists = Test-Path $envFile

if ($envExists) {
    Write-Host "✅ Found existing .env file" -ForegroundColor Green
    $overwrite = Read-Host "Do you want to update ServiceNow credentials? (y/n)"
    if ($overwrite -ne 'y') {
        Write-Host "Exiting without changes" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "📝 Please provide your ServiceNow credentials" -ForegroundColor Yellow
Write-Host "   (Get these from https://developer.servicenow.com/)" -ForegroundColor Gray
Write-Host ""

# Get ServiceNow credentials
$instanceUrl = Read-Host "ServiceNow Instance URL (e.g., https://dev12345.service-now.com)"
$username = Read-Host "ServiceNow Username (default: admin)"
$password = Read-Host "ServiceNow Password" -AsSecureString

if (-not $username) {
    $username = "admin"
}

# Convert secure string to plain text
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
$plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Read existing .env if it exists
$envContent = @()
if ($envExists) {
    $envContent = Get-Content $envFile | Where-Object { 
        $_ -notmatch '^SERVICENOW_' 
    }
}

# Add ServiceNow credentials
$envContent += ""
$envContent += "# ServiceNow Configuration"
$envContent += "SERVICENOW_INSTANCE_URL=$instanceUrl"
$envContent += "SERVICENOW_USERNAME=$username"
$envContent += "SERVICENOW_PASSWORD=$plainPassword"

# Write to .env file
$envContent | Out-File -FilePath $envFile -Encoding utf8

Write-Host ""
Write-Host "✅ ServiceNow credentials saved to .env file" -ForegroundColor Green
Write-Host ""

# Set environment variables for current session
$env:SERVICENOW_INSTANCE_URL = $instanceUrl
$env:SERVICENOW_USERNAME = $username
$env:SERVICENOW_PASSWORD = $plainPassword

Write-Host "✅ Environment variables set for current session" -ForegroundColor Green
Write-Host ""

# Test connection
Write-Host "🔍 Testing ServiceNow connection..." -ForegroundColor Yellow

$pair = "$($username):$($plainPassword)"
$encodedCreds = [System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($pair))
$headers = @{
    Authorization = "Basic $encodedCreds"
    "Content-Type" = "application/json"
}

$testUri = "$instanceUrl/api/now/table/incident?sysparm_limit=1"

try {
    $response = Invoke-RestMethod -Uri $testUri -Method Get -Headers $headers -ErrorAction Stop
    Write-Host "✅ Connection successful!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ Connection failed!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Please check:" -ForegroundColor Yellow
    Write-Host "   - Instance URL is correct" -ForegroundColor Gray
    Write-Host "   - Username and password are correct" -ForegroundColor Gray
    Write-Host "   - Instance is active (not hibernated)" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "🎉 ServiceNow setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run integration test:" -ForegroundColor White
Write-Host "     python test_servicenow_integration.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Restart the backend API:" -ForegroundColor White
Write-Host "     python src\slack_bot\slack_api_simple.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Create a transfer to see ServiceNow ticket creation:" -ForegroundColor White
Write-Host "     Visit http://localhost:5173 and create a transfer" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. View tickets in ServiceNow:" -ForegroundColor White
Write-Host "     $instanceUrl/incident_list.do" -ForegroundColor Gray
Write-Host ""
