# 🔧 Fix: Missing 'requests' Library in Lambda

## Problem

The `FileFerry-UpdateServiceNow` Lambda function is failing with:
```
Runtime.ImportModuleError: Unable to import module 'update_servicenow': No module named 'requests'
```

## Root Cause

The Lambda function code uses the `requests` library, but it wasn't included in the deployment package. Lambda Python runtime doesn't include `requests` by default.

## Solution

You have **3 options** to fix this:

---

## 🚀 Option 1: Quick Fix with CloudShell Script (RECOMMENDED)

**Time: 5 minutes**

### Steps:

1. **Open AWS CloudShell**
   - Go to: https://console.aws.amazon.com
   - Region: us-east-1
   - Click CloudShell icon

2. **Upload the fix script**
   - Click **Actions** → **Upload file**
   - Select: `FIX_UPDATE_SERVICENOW.sh`

3. **Run the script**
   ```bash
   chmod +x FIX_UPDATE_SERVICENOW.sh
   ./FIX_UPDATE_SERVICENOW.sh
   ```

**What it does:**
- Creates deployment package with `requests` library
- Updates Lambda function code
- Preserves your environment variables

**Expected output:**
```
🎉 Fix Applied Successfully!
✅ 'requests' library added
✅ Function code updated
```

---

## 📦 Option 2: Add Lambda Layer (Alternative)

**Time: 3 minutes**

Use AWS's managed Lambda Layer for requests:

### Steps:

1. **Go to Lambda Console**
   - Open `FileFerry-UpdateServiceNow`

2. **Scroll to Layers section**
   - Click **Add a layer**

3. **Select AWS Layers**
   - Choose: **AWSSDKPandas-Python311** (includes requests)
   - Or search for a requests-specific layer

4. **Save**

**Advantage:** No code redeployment needed

**Disadvantage:** Larger package size

---

## 🛠️ Option 3: Manual Package Creation

**Time: 10 minutes**

Create deployment package locally:

### Steps:

1. **Create package directory**
   ```powershell
   mkdir lambda-package
   cd lambda-package
   ```

2. **Install requests**
   ```powershell
   pip install --target . requests
   ```

3. **Add Lambda function code**
   - Copy `update_servicenow.py` to this directory

4. **Create ZIP**
   ```powershell
   Compress-Archive -Path * -DestinationPath ../lambda-package.zip
   ```

5. **Upload to Lambda**
   - AWS Console → Lambda → `FileFerry-UpdateServiceNow`
   - **Upload from** → `.zip file`
   - Select `lambda-package.zip`

---

## ✅ Verification

After applying the fix:

1. **Go to Lambda Console**
   - Open: `FileFerry-UpdateServiceNow`

2. **Test tab** → Run test

3. **Expected Success:**
   ```json
   {
     "status": "completed",
     "tickets_updated": 2
   }
   ```

4. **Check CloudWatch Logs**
   - Should see: "✅ Updated ticket: INC0010001"
   - No more import errors

---

## 🔍 Why This Happened

**During initial deployment**, the Lambda functions were created but the `requests` library wasn't packaged with `update_servicenow.py`.

**Common causes:**
- Lambda deployed without dependencies
- `requests` not in deployment package
- Missing `requirements.txt` during deployment

**Python packages NOT included in Lambda runtime:**
- requests
- boto3 (actually IS included)
- pandas
- numpy
- Most third-party packages

**Python packages included:**
- boto3 (AWS SDK)
- botocore
- Standard library (json, os, sys, etc.)

---

## 📋 Fix Verification Checklist

- [ ] Fix script uploaded to CloudShell
- [ ] Script executed successfully
- [ ] Lambda function updated (check Last Modified time)
- [ ] Test event executed without errors
- [ ] Response shows "tickets_updated": 2
- [ ] CloudWatch logs show successful ticket updates
- [ ] No "ImportModuleError" in logs

---

## 🚨 If Fix Fails

### Error: "pip3: command not found"
**Solution:** Use `pip` instead of `pip3` in script

### Error: "Access Denied"
**Solution:** Check IAM permissions for Lambda update

### Error: "Function not found"
**Solution:** Verify function name is exactly `FileFerry-UpdateServiceNow`

### Error: Still getting ImportModuleError
**Solution:**
1. Check Lambda handler is set to: `update_servicenow.lambda_handler`
2. Verify ZIP structure (files at root, not in subfolder)
3. Check Lambda runtime is Python 3.11 or 3.12

---

## 🎯 After Fix is Applied

Your Lambda should now work! Test end-to-end:

1. **Run demo.html** transfer
2. **Check ServiceNow** - Tickets should be updated
3. **Verify in CloudWatch** - No errors

---

## 📞 Quick Commands

**Check Lambda configuration:**
```bash
aws lambda get-function-configuration --function-name FileFerry-UpdateServiceNow
```

**View recent logs:**
```bash
aws logs tail /aws/lambda/FileFerry-UpdateServiceNow --follow
```

**Test Lambda:**
```bash
aws lambda invoke --function-name FileFerry-UpdateServiceNow --payload file://test.json response.json
```

---

**Ready to fix? Use Option 1 (CloudShell Script) - it's automated and fastest!** 🚀
