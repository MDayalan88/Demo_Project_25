# Add Lambda Layer - Quick Guide

## ⚡ Fastest Fix for ImportModuleError (3 minutes)

### Steps to Add Lambda Layer with 'requests' Library

**1. Open AWS Lambda Console**
   - Go to: https://us-east-1.console.aws.amazon.com/lambda
   - Click on **FileFerry-UpdateServiceNow** function

**2. Scroll to Layers Section**
   - In the function overview, scroll down to **Layers** section
   - Click **Add a layer** button

**3. Configure Layer**
   - Select: **Specify an ARN**
   - Paste this ARN:
     ```
     arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p311-requests:8
     ```
   - Click **Add**

**4. Wait for Update**
   - Function will update automatically (5-10 seconds)
   - You'll see the layer listed under "Layers (1)"

**5. Test Lambda Function**
   - Click **Test** tab
   - Use existing test event: **TestServiceNowUpdate**
   - Click **Test** button

**Expected Success Response:**
```json
{
  "status": "completed",
  "tickets_updated": 2,
  "updates": [
    {
      "ticket": "INC0010001",
      "sys_id": "...",
      "status": "success"
    },
    {
      "ticket": "INC0010002",
      "sys_id": "...",
      "status": "success"
    }
  ]
}
```

### Alternative Layer ARN (if first doesn't work)

If the first ARN doesn't work, try this one:
```
arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:18
```

This layer includes `requests` plus many other data science libraries.

### Verify in CloudWatch Logs

After testing, check logs:
1. Click **Monitor** tab
2. Click **View CloudWatch logs**
3. Click latest log stream
4. Look for: `✅ Updated ticket: INC0010001`

### Troubleshooting

**If layer doesn't work:**
- Check Python runtime: Should be Python 3.11
- Verify ARN is for us-east-1 region
- Try alternative ARN above
- Use FIX_UPDATE_SERVICENOW.sh script instead

**If test still fails:**
- Check environment variables are set
- Verify ServiceNow credentials are correct
- Check tickets exist in ServiceNow portal

---

## Next Steps After Fix

Once Lambda test succeeds:

1. ✅ **Create Real ServiceNow Tickets**
   - ServiceNow Portal → Incident → Create New
   - Create 2 test incidents
   - Note the INC numbers

2. ✅ **Test End-to-End Transfer**
   - Open demo.html: http://localhost:8000/demo.html
   - Start transfer with real S3 bucket
   - Use real ServiceNow ticket numbers

3. ✅ **Verify ServiceNow Updates**
   - Check tickets in ServiceNow portal
   - Verify work notes added
   - Verify state changed to "Resolved"

4. 🎉 **100% Complete!**

---

## Why This Works

Lambda Layers provide shared libraries that can be used by multiple functions:
- Layer contains pre-packaged `requests` library
- Lambda runtime loads layer before function code
- No redeployment of function code needed
- Layer is managed by AWS community (Klayers)

**Klayers** maintains up-to-date Lambda layers for popular Python packages:
- https://github.com/keithrozario/Klayers
- Layer includes: requests==2.31.0 + dependencies (urllib3, certifi, charset-normalizer, idna)
