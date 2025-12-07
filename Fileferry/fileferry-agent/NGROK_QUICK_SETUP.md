# ngrok Quick Setup - Share FileFerry Demo with Friend on Different Network

**Scenario**: Friend is on different Wi-Fi/location  
**Solution**: ngrok (free tunnel service)  
**Time**: 5 minutes  
**Cost**: Free

---

## 🚀 QUICK SETUP (3 STEPS)

### **Step 1: Download ngrok**

1. Go to: https://ngrok.com/download
2. Click "Download for Windows"
3. Extract the ZIP file to a folder (e.g., `C:\ngrok\`)

### **Step 2: Start Your Server** (if not running)

```powershell
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend
python -m http.server 8000
```

Keep this window open!

### **Step 3: Run ngrok**

Open a **NEW PowerShell window**:

```powershell
cd C:\ngrok   # or wherever you extracted it
.\ngrok http 8000
```

You'll see something like:

```
Session Status                online
Account                       Free (Limit: 40 connections/minute)
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8000

Connections                   0
```

### **Step 4: Share the URL**

Copy the **https** URL (e.g., `https://abc123.ngrok-free.app`)

Add `/demo.html` at the end:
```
https://abc123.ngrok-free.app/demo.html
```

**Send this to your friend!** 🎉

---

## 📋 COMPLETE EXAMPLE

```powershell
# Window 1: Start server
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend
python -m http.server 8000

# Window 2: Start ngrok
cd C:\ngrok
.\ngrok http 8000

# Share URL: https://YOUR-UNIQUE-ID.ngrok-free.app/demo.html
```

---

## ✅ ADVANTAGES

- ✅ **5-minute setup** (fastest)
- ✅ **Free** (no credit card)
- ✅ **HTTPS** (secure)
- ✅ **Works worldwide** (any network)
- ✅ **No router config** needed
- ✅ **No firewall changes** needed

---

## ⚠️ LIMITATIONS

- ⏱️ **Session expires** when you close ngrok
- 🔗 **New URL each time** (unless paid plan)
- 📊 **40 connections/minute** limit (free tier)
- 💻 **Your PC must stay on**

---

## 🔧 TROUBLESHOOTING

### **"ngrok not found"**
```powershell
# Make sure you're in the correct directory
cd C:\ngrok   # or wherever you extracted it
dir ngrok.exe # verify file exists
```

### **"Failed to start tunnel"**
- Check if port 8000 is in use:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000
  ```
- Make sure Python server is running on port 8000

### **Friend sees "ngrok warning page"**
- This is normal for free tier
- Click "Visit Site" button
- They'll see your demo

### **"Too many connections"**
- Free tier limit: 40/minute
- Upgrade to paid ($8/month) for unlimited
- Or use AWS S3 instead

---

## 💡 ALTERNATIVE: Localtunnel (Also Free)

If ngrok doesn't work, try localtunnel:

```powershell
# Install (requires Node.js/npm)
npm install -g localtunnel

# Run (make sure server is on port 8000)
lt --port 8000

# You'll get: https://xxx-xxx-xxx.loca.lt
```

---

## 🌐 FOR LONGER-TERM SHARING

If you need the demo available for days/weeks:

### **Option 1: AWS S3 (Manual via Web Console)**

1. Login to AWS Console: https://s3.console.aws.amazon.com
2. Create bucket: `fileferry-demo-YOURNAME`
3. Upload files from: `C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend`
4. Make public (uncheck "Block public access")
5. Enable static website hosting
6. Get URL: `http://fileferry-demo-YOURNAME.s3-website-us-east-1.amazonaws.com`

**Cost**: ~$0.50-$2/month  
**Uptime**: 24/7, 99.99% reliable

### **Option 2: GitHub Pages (Free, Permanent)**

```powershell
# Initialize git (if not already)
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend
git init
git add demo.html index.html
git commit -m "FileFerry demo"

# Create repo on GitHub
# Push to GitHub
git remote add origin https://github.com/YOUR-USERNAME/fileferry-demo.git
git branch -M main
git push -u origin main

# Enable GitHub Pages
# Settings > Pages > Source: main branch
# URL: https://YOUR-USERNAME.github.io/fileferry-demo/demo.html
```

**Cost**: Free  
**Uptime**: 24/7 permanent

---

## 🎯 RECOMMENDATION

### **For Quick Demo (Next 1-2 hours)**:
✅ **Use ngrok** (5 minutes, no account needed)

### **For Stakeholder Presentation (Next week)**:
✅ **Use AWS S3** (via web console, ~$1/month)

### **For Permanent Access**:
✅ **Use GitHub Pages** (free forever)

---

## 📞 GETTING STARTED NOW

**Quickest path (5 minutes)**:

1. **Download ngrok**: https://ngrok.com/download
2. **Extract** to `C:\ngrok\`
3. **Open 2 PowerShell windows**:

   Window 1:
   ```powershell
   cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend
   python -m http.server 8000
   ```

   Window 2:
   ```powershell
   cd C:\ngrok
   .\ngrok http 8000
   ```

4. **Copy the https:// URL** from ngrok output
5. **Add `/demo.html`** to the end
6. **Share with your friend!**

Example final URL:
```
https://abc123xyz.ngrok-free.app/demo.html
```

---

## 💬 MESSAGE TO SEND YOUR FRIEND

```
Hi! Check out the FileFerry AI Agent demo:

🌐 URL: https://YOUR-NGROK-URL.ngrok-free.app/demo.html

If you see a warning page, click "Visit Site" - it's safe!

Features to try:
- File transfer simulation (S3 to FTP/SFTP)
- AWS SSO authentication flow
- ServiceNow ticket creation
- 1TB file support visualization

Username is pre-filled (demo environment).

Let me know what you think!
```

---

**Created**: December 4, 2025  
**Use Case**: Share demo with friend on different network  
**Best Solution**: ngrok (free, 5 minutes)
