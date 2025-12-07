# FileFerry Agent Test - Simple Version

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "  FileFerry Agent Status Check" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

# Check 1: Python
Write-Host "✓ Python Version:" -ForegroundColor Green
python --version

# Check 2: Dependencies
Write-Host "`n✓ Checking Dependencies..." -ForegroundColor Green
python -c "import fastapi, uvicorn; print('  FastAPI and Uvicorn: OK')" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  ⚠️  FastAPI/Uvicorn not installed" -ForegroundColor Yellow }

python -c "import boto3; print('  Boto3 (AWS): OK')" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "  ⚠️  Boto3 not installed (optional)" -ForegroundColor Yellow }

# Check 3: Agent Files
Write-Host "`n✓ Agent Files:" -ForegroundColor Green
if (Test-Path "agent.py") { Write-Host "  ✅ agent.py" -ForegroundColor Green }
if (Test-Path "core-AI-Agent.py") { Write-Host "  ✅ core-AI-Agent.py" -ForegroundColor Green }
if (Test-Path "src\slack_bot\slack_api.py") { Write-Host "  ✅ Backend API (slack_api.py)" -ForegroundColor Green }
if (Test-Path "frontend\demo.html") { Write-Host "  ✅ UI Demo (demo.html)" -ForegroundColor Green }

# Check 4: ServiceNow Config
Write-Host "`n✓ ServiceNow Configuration:" -ForegroundColor Green
if ($env:SERVICENOW_INSTANCE_URL) { 
    Write-Host "  ✅ Instance: $env:SERVICENOW_INSTANCE_URL" -ForegroundColor Green 
} else { 
    Write-Host "  ⚠️  Instance URL not set" -ForegroundColor Yellow 
}

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host "  HOW TO TEST YOUR AGENT" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

Write-Host "OPTION 1: UI Demo (Quick - 5 min)" -ForegroundColor Yellow
Write-Host "  Run:" -ForegroundColor White
Write-Host "    Invoke-Item frontend\demo.html`n" -ForegroundColor Cyan

Write-Host "OPTION 2: Full Demo (Backend + UI - 15 min)" -ForegroundColor Yellow
Write-Host "  Terminal 1:" -ForegroundColor White
Write-Host "    python src\slack_bot\slack_api.py" -ForegroundColor Cyan
Write-Host "  Terminal 2:" -ForegroundColor White
Write-Host "    Invoke-Item frontend\demo.html`n" -ForegroundColor Cyan

Write-Host "OPTION 3: AI Agent Direct" -ForegroundColor Yellow
Write-Host "  Run:" -ForegroundColor White
Write-Host "    python agent.py`n" -ForegroundColor Cyan

Write-Host "=========================================`n" -ForegroundColor Cyan
Write-Host "📖 Full guides available:" -ForegroundColor White
Write-Host "   - DEMO_GUIDE.md (complete demo instructions)" -ForegroundColor Gray
Write-Host "   - DEMO_SCRIPT.md (quick reference)" -ForegroundColor Gray
Write-Host "   - MODERN_UI_GUIDE.md (UI documentation)" -ForegroundColor Gray
Write-Host ""
