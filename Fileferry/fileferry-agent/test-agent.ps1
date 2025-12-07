# FileFerry End-to-End Agent Test Script
# Run this to test your complete FileFerry agent setup

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  FileFerry Agent - End-to-End Test" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = "C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent"

# Test 1: Check Python and Dependencies
Write-Host "Test 1: Checking Python Environment..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✅ Python installed: $pythonVersion" -ForegroundColor Green
    
    # Check FastAPI/Uvicorn
    $deps = python -c "import fastapi, uvicorn; print('OK')" 2>&1
    if ($deps -like "*OK*") {
        Write-Host "  ✅ FastAPI and Uvicorn installed" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  FastAPI/Uvicorn not found" -ForegroundColor Yellow
    }
    
    # Check AWS Bedrock
    $bedrock = python -c "import boto3; print('OK')" 2>&1
    if ($bedrock -like "*OK*") {
        Write-Host "  ✅ Boto3 (AWS SDK) installed" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Boto3 not found (optional for full demo)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ Python not found or error occurred" -ForegroundColor Red
}
Write-Host ""

# Test 2: Check Agent Files
Write-Host "Test 2: Checking Agent Files..." -ForegroundColor Yellow
$agentFiles = @(
    "agent.py",
    "core-AI-Agent.py",
    "src\slack_bot\slack_api.py",
    "frontend\demo.html",
    "config\config.yaml"
)

foreach ($file in $agentFiles) {
    $fullPath = Join-Path $ProjectRoot $file
    if (Test-Path $fullPath) {
        Write-Host "  ✅ Found: $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Missing: $file" -ForegroundColor Red
    }
}
Write-Host ""

# Test 3: Check ServiceNow Configuration
Write-Host "Test 3: Checking ServiceNow Configuration..." -ForegroundColor Yellow
if ($env:SERVICENOW_INSTANCE_URL) {
    Write-Host "  ✅ Instance URL: $env:SERVICENOW_INSTANCE_URL" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  SERVICENOW_INSTANCE_URL not set" -ForegroundColor Yellow
}

if ($env:SERVICENOW_USERNAME) {
    Write-Host "  ✅ Username: $env:SERVICENOW_USERNAME" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  SERVICENOW_USERNAME not set" -ForegroundColor Yellow
}

if ($env:SERVICENOW_PASSWORD) {
    Write-Host "  ✅ Password: ***SET***" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  SERVICENOW_PASSWORD not set" -ForegroundColor Yellow
}
Write-Host ""

# Test 4: Check AWS Configuration (Optional)
Write-Host "Test 4: Checking AWS Configuration..." -ForegroundColor Yellow
if ($env:AWS_REGION) {
    Write-Host "  ✅ AWS Region: $env:AWS_REGION" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  AWS_REGION not set (optional)" -ForegroundColor Yellow
}

if ($env:AWS_ACCESS_KEY_ID) {
    Write-Host "  ✅ AWS credentials configured" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  AWS credentials not set (optional)" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Available Demo Options" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Option 1: UI Demo Only (No Backend Needed)" -ForegroundColor Green
Write-Host "  Command:" -ForegroundColor White
Write-Host "    Invoke-Item '$ProjectRoot\frontend\demo.html'" -ForegroundColor Gray
Write-Host "  What you'll test:" -ForegroundColor White
Write-Host "    - Login flow with authentication" -ForegroundColor Gray
Write-Host "    - Dashboard navigation" -ForegroundColor Gray
Write-Host "    - File transfer form with validation" -ForegroundColor Gray
Write-Host "    - AWS SSO authentication flow" -ForegroundColor Gray
Write-Host "    - Change request form" -ForegroundColor Gray
Write-Host "  Duration: 5 minutes" -ForegroundColor Cyan
Write-Host ""

Write-Host "Option 2: Backend API + UI Demo" -ForegroundColor Green
Write-Host "  Step 1 - Start Backend (Terminal 1):" -ForegroundColor White
Write-Host "    cd '$ProjectRoot'" -ForegroundColor Gray
Write-Host "    python src\slack_bot\slack_api.py" -ForegroundColor Gray
Write-Host "  Step 2 - Open UI (Terminal 2):" -ForegroundColor White
Write-Host "    Invoke-Item '$ProjectRoot\frontend\demo.html'" -ForegroundColor Gray
Write-Host "  Step 3 - Test API (Terminal 3):" -ForegroundColor White
Write-Host "    Invoke-RestMethod http://localhost:8000/" -ForegroundColor Gray
Write-Host "  What you'll test:" -ForegroundColor White
Write-Host "    - Full UI flow" -ForegroundColor Gray
Write-Host "    - REST API endpoints" -ForegroundColor Gray
Write-Host "    - ServiceNow integration" -ForegroundColor Gray
Write-Host "    - Transfer request creation" -ForegroundColor Gray
Write-Host "  Duration: 15 minutes" -ForegroundColor Cyan
Write-Host ""

Write-Host "Option 3: AI Agent Direct Test" -ForegroundColor Green
Write-Host "  Command:" -ForegroundColor White
Write-Host "    cd '$ProjectRoot'" -ForegroundColor Gray
Write-Host "    python agent.py" -ForegroundColor Gray
Write-Host "  What you'll test:" -ForegroundColor White
Write-Host "    - Direct AI agent interaction" -ForegroundColor Gray
Write-Host "    - Bedrock AI capabilities" -ForegroundColor Gray
Write-Host "    - Agent tools and functions" -ForegroundColor Gray
Write-Host "  Duration: 10 minutes" -ForegroundColor Cyan
Write-Host ""

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Quick Start Recommendation" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 Start with Option 1 (UI Demo) - It's ready to go!" -ForegroundColor Yellow
Write-Host ""

# Ask user what they want to do
Write-Host "What would you like to do?" -ForegroundColor Cyan
Write-Host "  1 - Open UI Demo (Recommended)" -ForegroundColor White
Write-Host "  2 - Start Backend + UI Demo" -ForegroundColor White
Write-Host "  3 - Test AI Agent Directly" -ForegroundColor White
Write-Host "  4 - Show detailed instructions" -ForegroundColor White
Write-Host "  Q - Quit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-4, Q)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Opening UI Demo..." -ForegroundColor Green
        Invoke-Item "$ProjectRoot\frontend\demo.html"
        Write-Host ""
        Write-Host "✅ Demo opened in browser" -ForegroundColor Green
        Write-Host "📋 Follow the demo flow in DEMO_GUIDE.md" -ForegroundColor Cyan
    }
    "2" {
        Write-Host ""
        Write-Host "Starting Backend Server..." -ForegroundColor Green
        Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
        Write-Host ""
        Set-Location $ProjectRoot
        python src\slack_bot\slack_api.py
    }
    "3" {
        Write-Host ""
        Write-Host "Starting AI Agent..." -ForegroundColor Green
        Write-Host ""
        Set-Location $ProjectRoot
        python agent.py
    }
    "4" {
        Write-Host ""
        Write-Host "Opening documentation..." -ForegroundColor Green
        $docs = @("DEMO_GUIDE.md", "DEMO_SCRIPT.md", "MODERN_UI_GUIDE.md")
        foreach ($doc in $docs) {
            $docPath = Join-Path $ProjectRoot $doc
            if (Test-Path $docPath) {
                Write-Host "  📖 $doc" -ForegroundColor Cyan
            }
        }
        Write-Host ""
        Write-Host "You can open these files in VS Code or any text editor" -ForegroundColor White
    }
    "Q" {
        Write-Host ""
        Write-Host "Goodbye! 👋" -ForegroundColor Cyan
    }
    default {
        Write-Host ""
        Write-Host "Invalid choice. Run the script again." -ForegroundColor Red
    }
}

Write-Host ""
