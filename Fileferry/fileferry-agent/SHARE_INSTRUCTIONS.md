# Share FileFerry Demo - Multiple Options

## Option 1: VS Code Port Forwarding (Easiest - If you have VS Code)

1. **Open VS Code** and this project
2. Go to **PORTS** tab (bottom panel)
3. Click "Forward a Port" button
4. Enter: `8000`
5. Right-click on port 8000 → **Port Visibility** → **Public**
6. Copy the forwarded URL (looks like: `https://xxx.devtunnels.ms/`)
7. Share this URL with your friends!

**Pros**: Built into VS Code, works through corporate firewall
**Cons**: Requires VS Code and GitHub login

---

## Option 2: localtunnel.me (No Installation - Works via NPX)

### If you have Node.js installed:

```powershell
# Start your Python server first (in one terminal)
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent
python -m http.server 8000

# In another terminal, create tunnel (no admin needed)
npx localtunnel --port 8000
```

This will give you a public URL like: `https://xyz-abc-123.loca.lt`

**Pros**: No installation, works through corporate proxies
**Cons**: Requires Node.js/npm

---

## Option 3: SSH Tunnel (If you have a personal VPS/Server)

If you have access to a personal server with SSH:

```powershell
ssh -R 80:localhost:8000 serveo.net
```

Or with your own server:
```powershell
ssh -R 8000:localhost:8000 your-server.com
```

---

## Option 4: Share on Local Network (No Internet Required)

### Find your IP address:
```powershell
ipconfig | Select-String "IPv4"
```

### Share with colleagues on same network:
```
http://YOUR-IP-ADDRESS:8000/demo.html
http://YOUR-IP-ADDRESS:8000/demo-hybrid.html
```

**Example**: `http://192.168.1.100:8000/demo.html`

**Pros**: Fast, secure, works without internet
**Cons**: Only works for people on same office network

---

## Option 5: Use Microsoft Dev Tunnels (Recommended for Office Environment)

Microsoft Dev Tunnels work well in corporate environments:

### Install (no admin needed):
```powershell
# Download to user folder
$devTunnelPath = "$env:USERPROFILE\devtunnel"
New-Item -ItemType Directory -Force -Path $devTunnelPath
cd $devTunnelPath

# Download devtunnel CLI (try this)
Invoke-WebRequest -Uri "https://aka.ms/devtunnelcliwin-x64" -OutFile "devtunnel.zip"
Expand-Archive -Path "devtunnel.zip" -DestinationPath "." -Force
```

### Create tunnel:
```powershell
.\devtunnel.exe user login
.\devtunnel.exe host -p 8000
```

---

## Recommended Approach for Your Situation:

Since you're on an office laptop with restricted admin access:

### **Try Option 1 (VS Code Port Forwarding) - Easiest!**

1. Open this project in VS Code
2. Press `Ctrl + Shift + P`
3. Type "Forward a Port"
4. Enter: 8000
5. Set to Public
6. Share the URL!

### **Or Try Option 4 (Local Network) - Instant!**

```powershell
# Get your IP
(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"}).IPAddress

# Share this URL format with colleagues:
# http://YOUR-IP:8000/demo.html
```

---

## Current Server Status

Your Python server should be running on:
- Local: http://localhost:8000/demo.html
- Local: http://localhost:8000/demo-hybrid.html

Make sure to keep the Python server running while sharing!
