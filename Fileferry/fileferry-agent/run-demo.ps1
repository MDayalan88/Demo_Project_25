# FileFerry Demo Automation Script
# This script helps you run the end-to-end demo

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("ui-only", "full", "test-api", "help")]
    [string]$DemoType = "help"
)

$ProjectRoot = "C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent"

function Show-Help {
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host "  FileFerry Demo Automation Script" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\run-demo.ps1 -DemoType <type>" -ForegroundColor White
    Write-Host ""
    Write-Host "Demo Types:" -ForegroundColor Yellow
    Write-Host "  ui-only   - Open UI demo only (5 min, no setup)" -ForegroundColor Green
    Write-Host "  full      - Start backend + UI (15 min demo)" -ForegroundColor Green
    Write-Host "  test-api  - Test backend API endpoints" -ForegroundColor Green
    Write-Host "  help      - Show this help message" -ForegroundColor Green
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\run-demo.ps1 -DemoType ui-only" -ForegroundColor White
    Write-Host "  .\run-demo.ps1 -DemoType full" -ForegroundColor White
    Write-Host ""
}

function Start-UIDemo {
    Write-Host "`n✨ Starting UI Demo..." -ForegroundColor Cyan
    Write-Host ""
    
    $demoFile = Join-Path $ProjectRoot "frontend\demo.html"
    
    if (Test-Path $demoFile) {
        Write-Host "✅ Opening demo.html in browser..." -ForegroundColor Green
        Start-Process $demoFile
        
        Write-Host ""
        Write-Host "📋 Demo Flow:" -ForegroundColor Yellow
        Write-Host "  1. Login with any username/password" -ForegroundColor White
        Write-Host "  2. Dashboard → Click 'FileFerry'" -ForegroundColor White
        Write-Host "  3. Fill form with test data" -ForegroundColor White
        Write-Host "  4. Submit → AWS SSO → Success" -ForegroundColor White
        Write-Host "  5. Return → Try 'Change Request'" -ForegroundColor White
        Write-Host ""
        Write-Host "⏱️  Estimated time: 5 minutes" -ForegroundColor Cyan
        Write-Host "📖 Full guide: DEMO_GUIDE.md" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Error: demo.html not found at $demoFile" -ForegroundColor Red
        Write-Host "Expected location: frontend\demo.html" -ForegroundColor Yellow
    }
}

function Start-FullDemo {
    Write-Host "`n🚀 Starting Full Demo (Backend + UI)..." -ForegroundColor Cyan
    Write-Host ""
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Python not found. Please install Python first." -ForegroundColor Red
        return
    }
    
    # Check dependencies
    Write-Host "Checking dependencies..." -ForegroundColor Yellow
    $depCheck = python -c "import fastapi, uvicorn; print('OK')" 2>&1
    if ($depCheck -like "*OK*") {
        Write-Host "✅ FastAPI and Uvicorn installed" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing dependencies. Installing..." -ForegroundColor Yellow
        pip install fastapi uvicorn python-dotenv pyyaml 2>&1 | Out-Null
    }
    
    Write-Host ""
    Write-Host "🔧 Setup Instructions:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Terminal 1 (Backend API):" -ForegroundColor Yellow
    Write-Host "  -------------------------" -ForegroundColor Gray
    Write-Host "  cd $ProjectRoot" -ForegroundColor White
    Write-Host "  python src\slack_bot\slack_api.py" -ForegroundColor White
    Write-Host ""
    Write-Host "  Terminal 2 (UI):" -ForegroundColor Yellow
    Write-Host "  ----------------" -ForegroundColor Gray
    Write-Host "  Start-Process '$ProjectRoot\frontend\demo.html'" -ForegroundColor White
    Write-Host ""
    Write-Host "  Terminal 3 (Test API):" -ForegroundColor Yellow
    Write-Host "  ---------------------" -ForegroundColor Gray
    Write-Host "  Invoke-RestMethod -Uri 'http://localhost:8000/' -Method Get" -ForegroundColor White
    Write-Host ""
    
    $response = Read-Host "Start backend now? (y/n)"
    if ($response -eq "y") {
        Write-Host ""
        Write-Host "Starting backend API server..." -ForegroundColor Cyan
        Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
        Write-Host ""
        
        Set-Location $ProjectRoot
        python src\slack_bot\slack_api.py
    } else {
        Write-Host ""
        Write-Host "✅ Instructions displayed. Start manually when ready." -ForegroundColor Green
        Write-Host "📖 Full guide: DEMO_GUIDE.md" -ForegroundColor Cyan
    }
}

function Test-API {
    Write-Host "`n🧪 Testing Backend API..." -ForegroundColor Cyan
    Write-Host ""
    
    $baseUrl = "http://localhost:8000"
    
    # Test 1: Health Check
    Write-Host "Test 1: Health Check" -ForegroundColor Yellow
    Write-Host "GET $baseUrl/" -ForegroundColor Gray
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/" -Method Get -TimeoutSec 5
        Write-Host "✅ Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed: Is backend running? Start with: python src\slack_bot\slack_api.py" -ForegroundColor Red
        return
    }
    Write-Host ""
    
    # Test 2: Transfer History
    Write-Host "Test 2: Transfer History" -ForegroundColor Yellow
    Write-Host "GET $baseUrl/api/transfer/history" -ForegroundColor Gray
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/api/transfer/history" -Method Get -TimeoutSec 5
        Write-Host "✅ Response: Found $($response.Count) transfers" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Warning: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    Write-Host ""
    
    # Test 3: ServiceNow Integration
    Write-Host "Test 3: ServiceNow Integration" -ForegroundColor Yellow
    Write-Host "GET $baseUrl/servicenow/test" -ForegroundColor Gray
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/servicenow/test" -Method Get -TimeoutSec 10
        Write-Host "✅ Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
        if ($response.ticket_number) {
            Write-Host "   Ticket Created: $($response.ticket_number)" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "⚠️  ServiceNow test failed (may need credentials): $($_.Exception.Message)" -ForegroundColor Yellow
    }
    Write-Host ""
    
    # Test 4: Create Transfer (Mock)
    Write-Host "Test 4: Create Transfer Request" -ForegroundColor Yellow
    Write-Host "POST $baseUrl/api/transfer/create" -ForegroundColor Gray
    $body = @{
        source_type = "s3"
        source_bucket = "test-bucket"
        source_key = "demo-file.csv"
        dest_type = "ftp"
        dest_host = "ftp.example.com"
        dest_path = "/uploads"
        priority = "high"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/api/transfer/create" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 5
        Write-Host "✅ Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
        if ($response.request_id) {
            Write-Host "   Request ID: $($response.request_id)" -ForegroundColor Cyan
        }
    } catch {
        Write-Host "⚠️  Warning: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    Write-Host ""
    
    Write-Host "✅ API Testing Complete" -ForegroundColor Green
    Write-Host "📖 Full API docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
}

# Main execution
Clear-Host

switch ($DemoType) {
    "ui-only" {
        Start-UIDemo
    }
    "full" {
        Start-FullDemo
    }
    "test-api" {
        Test-API
    }
    "help" {
        Show-Help
    }
    default {
        Show-Help
    }
}

Write-Host ""
