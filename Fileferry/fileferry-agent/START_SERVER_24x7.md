# FileFerry Demo - 24/7 Server Options

**Created**: December 4, 2025  
**Purpose**: Keep FileFerry demo UI running continuously

---

## 🎯 QUICK SUMMARY

| Option | Best For | Cost | Effort | Reliability |
|--------|----------|------|--------|-------------|
| **Windows Task Scheduler** | Local PC, Dev/Testing | Free | 5 min | ⭐⭐⭐ |
| **Windows Service (NSSM)** | Local PC, Production | Free | 10 min | ⭐⭐⭐⭐ |
| **AWS S3 Static Hosting** | Cloud, Stakeholders | ~$0.50/month | 15 min | ⭐⭐⭐⭐⭐ |
| **AWS Amplify** | Cloud, Auto-deploy | Free tier | 20 min | ⭐⭐⭐⭐⭐ |
| **Netlify/Vercel** | Cloud, Free, Easy | Free | 10 min | ⭐⭐⭐⭐⭐ |

**RECOMMENDED**: AWS S3 Static Hosting (most aligned with your AWS architecture)

---

## OPTION 1: Windows Task Scheduler (Easiest - Local PC) ✅

**Best for**: Running on your local PC 24/7, quick setup

### **Setup Steps**:

1. **Create startup script**: `start-demo-server.ps1`
2. **Configure Task Scheduler** to run on:
   - System startup
   - User login
   - Auto-restart on failure

### **Step-by-Step**:

#### **1. Create PowerShell Script**:

```powershell
# Save as: C:\Martin-Files\Training\Demo\End-End\Fileferry\start-demo-server.ps1

# Configuration
$projectPath = "C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend"
$port = 8000
$logFile = "C:\Martin-Files\Training\Demo\End-End\Fileferry\server.log"

# Function to write logs
function Write-Log {
    param($message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $message" | Out-File -Append -FilePath $logFile
    Write-Host $message
}

# Start server
Write-Log "Starting FileFerry Demo Server..."

Set-Location $projectPath

# Kill any existing Python servers on port 8000
$existingProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    (Get-NetTCPConnection -OwningProcess $_.Id -ErrorAction SilentlyContinue).LocalPort -eq $port
}
if ($existingProcess) {
    Write-Log "Stopping existing server (PID: $($existingProcess.Id))..."
    Stop-Process -Id $existingProcess.Id -Force
    Start-Sleep -Seconds 2
}

# Get IP address
$ip = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias 'Wi-Fi*','Ethernet*' -ErrorAction SilentlyContinue | Select-Object -First 1).IPAddress

Write-Log "Server starting on port $port"
Write-Log "Access at: http://localhost:$port/demo.html"
Write-Log "Network access: http://${ip}:$port/demo.html"

# Start HTTP server (will run indefinitely)
try {
    python -m http.server $port 2>&1 | Tee-Object -Append -FilePath $logFile
} catch {
    Write-Log "ERROR: Server crashed - $_"
    # Auto-restart after 5 seconds
    Start-Sleep -Seconds 5
    & $PSCommandPath  # Restart this script
}
```

#### **2. Create Task Scheduler Entry**:

Run this in PowerShell **as Administrator**:

```powershell
# Create scheduled task to run server 24/7
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"C:\Martin-Files\Training\Demo\End-End\Fileferry\start-demo-server.ps1`""

$trigger1 = New-ScheduledTaskTrigger -AtStartup
$trigger2 = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -RestartCount 999

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType S4U -RunLevel Highest

Register-ScheduledTask `
    -TaskName "FileFerry-Demo-Server" `
    -Action $action `
    -Trigger $trigger1,$trigger2 `
    -Settings $settings `
    -Principal $principal `
    -Description "Runs FileFerry demo server 24/7 on port 8000" `
    -Force

Write-Host "✓ Task created! Server will start automatically." -ForegroundColor Green
Write-Host "  Task Name: FileFerry-Demo-Server" -ForegroundColor Cyan
Write-Host "  To start now: Start-ScheduledTask -TaskName 'FileFerry-Demo-Server'" -ForegroundColor Yellow
```

#### **3. Start the Task**:

```powershell
Start-ScheduledTask -TaskName "FileFerry-Demo-Server"
```

#### **4. Verify**:

```powershell
# Check task status
Get-ScheduledTask -TaskName "FileFerry-Demo-Server"

# Check if server is running
Get-Process python

# Test access
Start-Process "http://localhost:8000/demo.html"
```

#### **Management Commands**:

```powershell
# Stop server
Stop-ScheduledTask -TaskName "FileFerry-Demo-Server"

# Restart server
Stop-ScheduledTask -TaskName "FileFerry-Demo-Server"
Start-ScheduledTask -TaskName "FileFerry-Demo-Server"

# Remove task
Unregister-ScheduledTask -TaskName "FileFerry-Demo-Server" -Confirm:$false

# View logs
Get-Content "C:\Martin-Files\Training\Demo\End-End\Fileferry\server.log" -Tail 50
```

**Pros**: ✅ Free, Easy, Runs on your PC  
**Cons**: ⚠️ Requires PC to stay on, Not accessible if PC sleeps

---

## OPTION 2: Windows Service (Most Reliable - Local PC) ⭐ RECOMMENDED FOR LOCAL

**Best for**: Production-like setup on local PC, auto-restart, runs even when logged out

### **Using NSSM (Non-Sucking Service Manager)**:

#### **1. Download NSSM**:

```powershell
# Download NSSM
Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile "$env:TEMP\nssm.zip"
Expand-Archive -Path "$env:TEMP\nssm.zip" -DestinationPath "$env:TEMP\nssm"
Copy-Item "$env:TEMP\nssm\nssm-2.24\win64\nssm.exe" -Destination "C:\Windows\System32\"

Write-Host "✓ NSSM installed" -ForegroundColor Green
```

#### **2. Create Service**:

Run as **Administrator**:

```powershell
# Install service
nssm install FileFerryDemo python "-m" "http.server" "8000"

# Configure service
nssm set FileFerryDemo AppDirectory "C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend"
nssm set FileFerryDemo DisplayName "FileFerry Demo Server"
nssm set FileFerryDemo Description "FileFerry AI Agent Demo UI - 24/7 Server"
nssm set FileFerryDemo Start SERVICE_AUTO_START
nssm set FileFerryDemo AppStdout "C:\Martin-Files\Training\Demo\End-End\Fileferry\service.log"
nssm set FileFerryDemo AppStderr "C:\Martin-Files\Training\Demo\End-End\Fileferry\service-error.log"
nssm set FileFerryDemo AppRotateFiles 1
nssm set FileFerryDemo AppRotateOnline 1
nssm set FileFerryDemo AppRotateBytes 1048576  # 1MB

# Start service
nssm start FileFerryDemo

Write-Host "✓ Service created and started!" -ForegroundColor Green
Write-Host "  Access at: http://localhost:8000/demo.html" -ForegroundColor Cyan
```

#### **3. Service Management**:

```powershell
# Check status
nssm status FileFerryDemo

# Start service
nssm start FileFerryDemo

# Stop service
nssm stop FileFerryDemo

# Restart service
nssm restart FileFerryDemo

# Remove service
nssm remove FileFerryDemo confirm

# View logs
Get-Content "C:\Martin-Files\Training\Demo\End-End\Fileferry\service.log" -Tail 50
```

**Pros**: ✅ True 24/7, Auto-restart, Runs when logged out, Survives reboots  
**Cons**: ⚠️ Requires PC to stay on, Admin privileges needed

---

## OPTION 3: AWS S3 Static Hosting ⭐ RECOMMENDED FOR CLOUD

**Best for**: Stakeholder access, production deployment, aligns with AWS architecture

### **Why S3?**:
- ✅ **True 24/7 availability** (99.99% uptime SLA)
- ✅ **Global CDN** via CloudFront (optional)
- ✅ **HTTPS support**
- ✅ **~$0.50/month** for hosting + bandwidth
- ✅ **No server management**
- ✅ **Integrates with your AWS setup**

### **Setup Steps**:

#### **1. Create S3 Bucket & Upload**:

```powershell
# Set variables
$bucketName = "fileferry-demo-ui"  # Must be globally unique
$region = "us-east-1"

# Create bucket
aws s3 mb s3://$bucketName --region $region

# Configure as static website
aws s3 website s3://$bucketName `
    --index-document demo.html `
    --error-document demo.html

# Upload demo files
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend
aws s3 sync . s3://$bucketName --exclude "node_modules/*" --exclude "package*.json"

# Make bucket public (for demo access)
aws s3api put-bucket-policy --bucket $bucketName --policy @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$bucketName/*"
    }
  ]
}
"@

Write-Host "`n✓ S3 Static Website Created!" -ForegroundColor Green
Write-Host "  URL: http://$bucketName.s3-website-$region.amazonaws.com" -ForegroundColor Cyan
```

#### **2. (Optional) Add CloudFront for HTTPS**:

```powershell
# Create CloudFront distribution
$originDomain = "$bucketName.s3-website-$region.amazonaws.com"

aws cloudfront create-distribution `
    --origin-domain-name $originDomain `
    --default-root-object demo.html

Write-Host "✓ CloudFront distribution created (HTTPS enabled)" -ForegroundColor Green
Write-Host "  Wait 15-20 minutes for deployment" -ForegroundColor Yellow
Write-Host "  Get URL: aws cloudfront list-distributions --query 'DistributionList.Items[0].DomainName'" -ForegroundColor Cyan
```

#### **3. Update Demo (when needed)**:

```powershell
# Sync changes to S3
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend
aws s3 sync . s3://$bucketName --exclude "node_modules/*" --delete

Write-Host "✓ Demo updated!" -ForegroundColor Green
```

**Pros**: ✅ True cloud hosting, 24/7, HTTPS, Global CDN, No server maintenance  
**Cons**: ⚠️ Costs ~$0.50-$5/month (depending on traffic)

---

## OPTION 4: AWS Amplify (Best for CI/CD) ⭐ RECOMMENDED FOR AUTO-DEPLOY

**Best for**: Automatic deployments from Git, production-ready, full AWS integration

### **Setup**:

#### **1. Initialize Amplify**:

```powershell
# Install Amplify CLI (if not installed)
npm install -g @aws-amplify/cli

# Initialize project
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent
amplify init

# Add hosting
amplify add hosting

# Select:
# - Hosting with Amplify Console
# - Manual deployment (or connect to Git)

# Publish
amplify publish
```

#### **2. Connect to GitHub (for auto-deploy)**:

1. Push your code to GitHub (MDayalan88/Demo_Project_25)
2. Go to AWS Amplify Console: https://console.aws.amazon.com/amplify/
3. Click "New app" → "Host web app"
4. Select GitHub → Authorize → Select repo `Demo_Project_25`
5. Build settings:
   ```yaml
   version: 1
   frontend:
     phases:
       build:
         commands:
           - echo "Static site - no build needed"
     artifacts:
       baseDirectory: fileferry-agent/frontend
       files:
         - '**/*'
     cache:
       paths: []
   ```
6. Deploy!

**Amplify will now auto-deploy on every Git push!**

**Pros**: ✅ Auto-deploy from Git, HTTPS, CDN, Preview URLs, Free tier (1000 build mins/month)  
**Cons**: ⚠️ Requires Git setup, Costs after free tier

---

## OPTION 5: Netlify/Vercel (Easiest Cloud Option) ⭐ RECOMMENDED FOR QUICK DEMO

**Best for**: Quick cloud deployment, free, no AWS account needed

### **Netlify Setup (2 minutes)**:

#### **1. Install Netlify CLI**:

```powershell
npm install -g netlify-cli
```

#### **2. Deploy**:

```powershell
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend

# Login to Netlify
netlify login

# Deploy
netlify deploy --prod

# Follow prompts:
# - Create new site? Yes
# - Publish directory: . (current directory)

# Your site is live!
# Example: https://fileferry-demo-abc123.netlify.app
```

### **Vercel Setup (2 minutes)**:

```powershell
# Install Vercel CLI
npm install -g vercel

# Deploy
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend
vercel --prod

# Your site is live!
# Example: https://fileferry-demo.vercel.app
```

**Pros**: ✅ Free, 1-command deploy, HTTPS, Global CDN, Auto-deploy from Git  
**Cons**: ⚠️ Not on AWS (if that matters for your stakeholders)

---

## 📊 COMPARISON TABLE

| Feature | Task Scheduler | Windows Service | S3 Static | Amplify | Netlify/Vercel |
|---------|---------------|-----------------|-----------|---------|----------------|
| **Setup Time** | 5 min | 10 min | 15 min | 20 min | 2 min |
| **Cost** | Free | Free | ~$0.50/mo | Free tier | Free |
| **Reliability** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **HTTPS** | ❌ | ❌ | Optional | ✅ | ✅ |
| **Global CDN** | ❌ | ❌ | Optional | ✅ | ✅ |
| **Auto-restart** | ✅ | ✅ | N/A | N/A | N/A |
| **Remote Access** | ⚠️ Port forward | ⚠️ Port forward | ✅ | ✅ | ✅ |
| **Runs when logged out** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Survives PC shutdown** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **AWS Integration** | ❌ | ❌ | ✅✅✅ | ✅✅✅ | ❌ |
| **CI/CD from Git** | ❌ | ❌ | Manual | ✅ | ✅ |

---

## 🎯 RECOMMENDATIONS BY USE CASE

### **For Local Development (PC stays on)**:
✅ **Windows Service (NSSM)** - Most reliable for local 24/7

### **For Stakeholder Demos (need URL to share)**:
✅ **AWS S3 Static Hosting** - Best alignment with your AWS architecture

### **For Production (public access needed)**:
✅ **AWS Amplify** - Auto-deploy, HTTPS, monitoring, AWS integration

### **For Quick Testing (2-minute setup)**:
✅ **Netlify or Vercel** - Deploy in one command, free forever

---

## 🚀 QUICK START COMMANDS

### **Option 1: Local PC (Task Scheduler)**
```powershell
# Run as Administrator
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/your-repo/start-demo-server.ps1" -OutFile "C:\start-demo-server.ps1"
Register-ScheduledTask -TaskName "FileFerry-Demo" -Action (New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\start-demo-server.ps1") -Trigger (New-ScheduledTaskTrigger -AtStartup)
Start-ScheduledTask -TaskName "FileFerry-Demo"
```

### **Option 2: AWS S3 (Quick Deploy)**
```powershell
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend
aws s3 mb s3://fileferry-demo-ui-$((Get-Date).ToString('yyyyMMddHHmmss'))
$bucket = (aws s3 ls | Select-String "fileferry-demo-ui" | Select-Object -Last 1).ToString().Split()[-1]
aws s3 website s3://$bucket --index-document demo.html
aws s3 sync . s3://$bucket --acl public-read
Write-Host "Live at: http://$bucket.s3-website-us-east-1.amazonaws.com"
```

### **Option 3: Netlify (Fastest)**
```powershell
npm install -g netlify-cli
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent\frontend
netlify deploy --prod
```

---

## 📋 POST-DEPLOYMENT CHECKLIST

After setting up 24/7 hosting:

- [ ] Test demo URL from different devices
- [ ] Verify username "MartinDayalan" is locked
- [ ] Test logout functionality
- [ ] Check 1TB file visualization
- [ ] Verify AWS SSO page timer (60 seconds)
- [ ] Test ServiceNow ticket creation
- [ ] Share URL with stakeholders
- [ ] Set up monitoring/alerts (for cloud options)
- [ ] Document URL in DEPLOYMENT_PLAN.md
- [ ] Add URL to README.md

---

## 🆘 TROUBLESHOOTING

### **Local PC Issues**:

**Server not starting**:
```powershell
# Check if Python installed
python --version

# Check if port 8000 is free
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

# Kill process using port 8000
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force
```

**Can't access from other devices**:
```powershell
# Allow Python through firewall
New-NetFirewallRule -DisplayName "Python HTTP Server" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000
```

### **AWS S3 Issues**:

**403 Forbidden**:
```powershell
# Make bucket public
aws s3api put-public-access-block --bucket $bucketName --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
```

**Static website not working**:
```powershell
# Enable static website hosting
aws s3 website s3://$bucketName --index-document demo.html
```

---

## 💰 COST BREAKDOWN

### **Local PC Options** (Task Scheduler / Windows Service):
- **Cost**: $0
- **Additional**: Electricity (~$5-10/month if PC runs 24/7)

### **AWS S3 Static Hosting**:
- **Storage**: $0.023/GB (demo.html = 106KB = ~$0.002/month)
- **Requests**: $0.0004/1000 GET (100 views/day = ~$0.01/month)
- **Data Transfer**: $0.09/GB (10GB/month = ~$0.90/month)
- **Total**: **~$0.50-$2/month** for typical demo usage

### **AWS Amplify**:
- **Build**: Free for 1000 mins/month (static site = 0 mins)
- **Hosting**: $0.15/GB storage + $0.15/GB transfer
- **Total**: **Free tier sufficient** for demos

### **Netlify/Vercel**:
- **Free tier**: 100GB bandwidth/month
- **Total**: **$0** (unlimited for static sites)

---

## 🎯 MY RECOMMENDATION FOR YOU

Based on your FileFerry project context:

### **Immediate (Today)**: 
Use **Windows Service (NSSM)** for local 24/7 access while you work

### **This Week (For Stakeholders)**: 
Deploy to **AWS S3 Static Hosting** - aligns with your AWS architecture, professional URL, HTTPS optional

### **Next Week (Production)**: 
Set up **AWS Amplify** with GitHub auto-deploy - integrates with your deployment plan

---

## 📞 SUPPORT

For issues:
1. Check logs: `C:\Martin-Files\Training\Demo\End-End\Fileferry\server.log`
2. Verify Python: `python --version`
3. Check port: `Get-NetTCPConnection -LocalPort 8000`
4. Test locally: `http://localhost:8000/demo.html`
5. Check firewall: Windows Defender Firewall → Allow app

---

**Created**: December 4, 2025  
**Last Updated**: December 4, 2025  
**Maintained By**: FileFerry Team
