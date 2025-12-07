# Quick Firewall Fix for FileFerry Demo Server
# Run this as Administrator to allow network access to port 8000

Write-Host "🔥 FileFerry - Adding Firewall Rule for Port 8000" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run PowerShell as Administrator and try again:" -ForegroundColor Yellow
    Write-Host "   1. Right-click PowerShell" -ForegroundColor White
    Write-Host "   2. Select 'Run as Administrator'" -ForegroundColor White
    Write-Host "   3. Navigate to this folder and run the script again" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

Write-Host "✅ Running with Administrator privileges" -ForegroundColor Green
Write-Host ""

# Check if rule already exists
$existingRule = Get-NetFirewallRule -DisplayName "FileFerry Demo Server (Port 8000)" -ErrorAction SilentlyContinue

if ($existingRule) {
    Write-Host "⚠️  Firewall rule already exists. Removing old rule..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName "FileFerry Demo Server (Port 8000)"
    Write-Host "✅ Old rule removed" -ForegroundColor Green
    Write-Host ""
}

# Add new firewall rule
try {
    Write-Host "🔓 Adding firewall rule for port 8000..." -ForegroundColor Yellow
    
    New-NetFirewallRule `
        -DisplayName "FileFerry Demo Server (Port 8000)" `
        -Direction Inbound `
        -Action Allow `
        -Protocol TCP `
        -LocalPort 8000 `
        -Profile Any `
        -Description "Allow incoming HTTP connections to FileFerry demo server on port 8000"
    
    Write-Host ""
    Write-Host "✅ SUCCESS! Firewall rule added" -ForegroundColor Green
    Write-Host ""
    Write-Host "📡 Port 8000 is now accessible from other devices on your network" -ForegroundColor Cyan
    Write-Host ""
    
    # Get local IP
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -like "192.168.*" } | Select-Object -First 1).IPAddress
    
    if ($localIP) {
        Write-Host "🌐 Your network IP address: $localIP" -ForegroundColor Green
        Write-Host ""
        Write-Host "Access from other devices using:" -ForegroundColor Yellow
        Write-Host "   http://${localIP}:8000/frontend/demo.html" -ForegroundColor Cyan
        Write-Host "   http://${localIP}:8000/frontend/demo-hybrid.html" -ForegroundColor Cyan
    }
    
} catch {
    Write-Host "❌ Failed to add firewall rule: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Done! You can now start the server with: .\start-demo-server.ps1" -ForegroundColor Green
Write-Host ""
pause
