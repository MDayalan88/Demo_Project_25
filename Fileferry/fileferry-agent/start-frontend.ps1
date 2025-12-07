# FileFerry React UI - Quick Start Script

Write-Host "🚀 FileFerry Slack React Frontend - Quick Start" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
$nodeVersion = node --version 2>$null
if (-not $nodeVersion) {
    Write-Host "❌ Node.js not found. Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Node.js version: $nodeVersion" -ForegroundColor Green

# Check if Python is installed
$pythonVersion = python --version 2>$null
if (-not $pythonVersion) {
    Write-Host "❌ Python not found. Please install Python 3.11+ from https://www.python.org/" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Python version: $pythonVersion" -ForegroundColor Green

Write-Host ""
Write-Host "📦 Installing Frontend Dependencies..." -ForegroundColor Yellow
Set-Location frontend

if (-not (Test-Path "node_modules")) {
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Frontend installation failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✅ Frontend dependencies already installed" -ForegroundColor Green
}

# Create .env if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "📝 Creating .env file..." -ForegroundColor Yellow
    @"
VITE_API_URL=http://localhost:8000/api
VITE_DEBUG=true
"@ | Out-File -FilePath ".env" -Encoding utf8
    Write-Host "✅ .env file created" -ForegroundColor Green
}

Set-Location ..

Write-Host ""
Write-Host "📦 Installing Backend Dependencies..." -ForegroundColor Yellow

# Check if FastAPI is installed
$fastapiInstalled = pip show fastapi 2>$null
if (-not $fastapiInstalled) {
    pip install fastapi uvicorn python-multipart
    Write-Host "✅ Backend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✅ Backend dependencies already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1. Start Backend API (in one terminal):" -ForegroundColor White
Write-Host "     cd src\slack_bot" -ForegroundColor Gray
Write-Host "     python slack_api.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Start Frontend UI (in another terminal):" -ForegroundColor White
Write-Host "     cd frontend" -ForegroundColor Gray
Write-Host "     npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Open browser:" -ForegroundColor White
Write-Host "     http://localhost:5173" -ForegroundColor Gray
Write-Host ""
Write-Host "📚 Documentation: frontend/README.md" -ForegroundColor Cyan
Write-Host ""
