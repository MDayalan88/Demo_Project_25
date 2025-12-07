# 🚀 Quick Start Guide - Access FileFerry from Network

## Issue Fixed ✅
1. **Bell icon** - Now visible above the URL box (moved to `bottom: 100px`)
2. **Network access** - Solution provided below

---

## 📱 Access FileFerry UI from Other Devices

### Step 1: Start the HTTP Server

Open PowerShell in this directory and run:
```powershell
.\start-demo-server.ps1
```

This will:
- Start a Python HTTP server on port 8000
- Show your local IP address (e.g., 192.168.29.169)
- Display access URLs

### Step 2: Fix Firewall (If needed)

If you **cannot** access from other devices, you need to allow port 8000 through Windows Firewall.

**Run PowerShell as Administrator** and execute:
```powershell
.\fix-firewall.ps1
```

This will:
- Add a firewall rule to allow port 8000
- Enable network access from other devices

---

## 🌐 Access URLs

After starting the server, access from:

### **Same Computer:**
- 📄 **Demo (AWS Only):** http://localhost:8000/frontend/demo.html
- 🔀 **Demo Hybrid (AWS + Azure):** http://localhost:8000/frontend/demo-hybrid.html

### **Other Devices on Same Network:**
- 📄 **Demo (AWS Only):** http://192.168.29.169:8000/frontend/demo.html
- 🔀 **Demo Hybrid (AWS + Azure):** http://192.168.29.169:8000/frontend/demo-hybrid.html

**Note:** Replace `192.168.29.169` with your actual local IP (shown when you run `start-demo-server.ps1`)

---

## 🔍 Troubleshooting

### Server Not Starting?
```powershell
# Check if Python is installed
python --version

# If not found, install Python from https://www.python.org/
```

### Cannot Access from Network?
1. Make sure firewall rule is added (run `fix-firewall.ps1` as Administrator)
2. Check your IP address:
   ```powershell
   ipconfig
   # Look for "IPv4 Address" under your Wi-Fi or Ethernet adapter
   ```
3. Make sure both devices are on the same network

### Port 8000 Already in Use?
```powershell
# Stop the existing process using port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Or use a different port
python -m http.server 8080
# Then access: http://localhost:8080/frontend/demo.html
```

---

## ✅ What Was Fixed

### 1. Bell Icon Issue
**Problem:** Notification bell was hidden behind the URL info box  
**Solution:** Moved notification center from `bottom: 20px` to `bottom: 100px`

**Both files updated:**
- ✅ frontend/demo.html
- ✅ frontend/demo-hybrid.html

### 2. Network Access Issue
**Problem:** `http://192.168.29.169:8000/demo.html` not accessible  
**Root Cause:** 
- HTTP server not running
- Windows Firewall blocking port 8000

**Solution Provided:**
- ✅ `start-demo-server.ps1` - Starts HTTP server
- ✅ `fix-firewall.ps1` - Adds firewall rule

---

## 📋 Quick Commands

```powershell
# Start server
.\start-demo-server.ps1

# Fix firewall (as Administrator)
.\fix-firewall.ps1

# Open in browser
Start-Process "http://localhost:8000/frontend/demo.html"
```

---

## 🎉 Ready to Demo!

1. Run `.\start-demo-server.ps1`
2. Open browser to http://localhost:8000/frontend/demo.html
3. Bell icon is now visible above the URL box
4. Share network URL with others: http://YOUR_IP:8000/frontend/demo.html
