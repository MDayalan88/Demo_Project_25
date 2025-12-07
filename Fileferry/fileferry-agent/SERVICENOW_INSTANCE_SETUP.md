# FileFerry ServiceNow Setup - Quick Reference

## ✅ Configuration Complete

Your ServiceNow instance URL has been configured: **https://dev329630.service-now.com**

## 📋 Remaining Steps

### 1. Edit .env File with Your Password

```powershell
# Open .env file
notepad .env
```

Replace `your-password-here` with your actual ServiceNow admin password:
```
SERVICENOW_INSTANCE_URL=https://dev329630.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=YOUR_ACTUAL_PASSWORD
```

Save and close the file.

### 2. Wake Up Your ServiceNow Instance (If Needed)

Your instance may be hibernated. To wake it:
1. Visit: https://developer.servicenow.com/
2. Sign in
3. Click "Manage" → "Instance"
4. If hibernating, click "Wake Up"
5. Wait 1-2 minutes

### 3. Create DataOps Assignment Group

1. Log into: https://dev329630.service-now.com
2. Search for "Groups" in filter navigator
3. Go to: User Administration → Groups
4. Click "New"
5. Set Name: `DataOps`
6. Save and add yourself as member

### 4. Test Connection

```powershell
python test_servicenow_integration.py
```

Expected: ✅ All tests pass

### 5. Start Backend

```powershell
python .\src\slack_bot\slack_api_simple.py
```

Look for:
```
✅ ServiceNow integration ENABLED
   Instance: https://dev329630.service-now.com
```

### 6. Start Frontend (After Node.js Installation)

```powershell
cd frontend
npm install
npm run dev
```

Access: http://localhost:5173

## 🔧 Troubleshooting

**401 Unauthorized?**
- Check password in `.env` is correct
- Wake up instance (Step 2)
- Try password reset at developer portal

**Connection Timeout?**
- Instance is hibernated - wake it up
- Check internet connection
- Verify URL is correct (dev329630)

**Assignment Group Error?**
- Create "DataOps" group (Step 3)
- Or modify `SERVICENOW_ASSIGNMENT_GROUP` in backend code

## 🚀 Quick Start Commands

```powershell
# 1. Edit password in .env
notepad .env

# 2. Test connection
python test_servicenow_integration.py

# 3. Start backend
python .\src\slack_bot\slack_api_simple.py

# 4. Start frontend (new terminal)
cd frontend; npm run dev
```

## 📚 Documentation

- Full Setup: `SERVICENOW_SETUP.md`
- Troubleshooting: `SERVICENOW_TROUBLESHOOTING.md`
- Frontend Integration: `FRONTEND_SERVICENOW_INTEGRATION.md`

---

**Your Instance**: https://dev329630.service-now.com
