# FileFerry Demo Server - Start HTTP Server
# This script starts a Python HTTP server to serve the demo HTML files

Write-Host "🚀 Starting FileFerry Demo Server..." -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "❌ Python not found. Please install Python from https://www.python.org/" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python found: $($pythonCmd.Source)" -ForegroundColor Green
Write-Host ""

# Get local IP address
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -like "192.168.*" } | Select-Object -First 1).IPAddress

if (-not $localIP) {
    $localIP = "localhost"
}

Write-Host "📡 Network Information:" -ForegroundColor Yellow
Write-Host "   Local IP: $localIP" -ForegroundColor White
Write-Host "   Port: 8000" -ForegroundColor White
Write-Host ""

Write-Host "🌐 Access URLs:" -ForegroundColor Green
Write-Host "" 
Write-Host "   📄 Demo (AWS Only):" -ForegroundColor Yellow
Write-Host "      Local:    http://localhost:8000/frontend/demo.html" -ForegroundColor Cyan
Write-Host "      Network:  http://${localIP}:8000/frontend/demo.html" -ForegroundColor Cyan
Write-Host "" 
Write-Host "   🔀 Demo Hybrid (AWS + Azure):" -ForegroundColor Yellow
Write-Host "      Local:    http://localhost:8000/frontend/demo-hybrid.html" -ForegroundColor Cyan
Write-Host "      Network:  http://${localIP}:8000/frontend/demo-hybrid.html" -ForegroundColor Cyan
Write-Host ""

Write-Host "⚠️  IMPORTANT: If accessing from another device fails:" -ForegroundColor Yellow
Write-Host "   1. Check Windows Firewall settings" -ForegroundColor White
Write-Host "   2. Run: New-NetFirewallRule -DisplayName 'FileFerry Port 8000' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000" -ForegroundColor White
Write-Host ""

Write-Host "🔥 Starting HTTP server... (Press Ctrl+C to stop)" -ForegroundColor Green
Write-Host ""

# Change to the project directory
Set-Location $PSScriptRoot

# Start Python HTTP server
try {
    python -m http.server 8000
} catch {
    Write-Host "❌ Server stopped or error occurred: $_" -ForegroundColor Red
}
