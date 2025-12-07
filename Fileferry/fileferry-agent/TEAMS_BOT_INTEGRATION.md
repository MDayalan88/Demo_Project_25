# 🤖 Microsoft Teams Bot Integration Guide

## ✅ Yes! You Can Use Teams Bot with FileFerry

You have **TWO options** to integrate Microsoft Teams:

---

## 🎯 **Option 1: Teams Bot via Azure Bot Service (Traditional)**

### What You Get:
- Chat directly with FileFerry in Teams
- Natural language file transfer requests
- Adaptive Cards for rich UI
- Conversation history
- Bot appears in Teams search

### Time Required: **35-45 minutes**

### Prerequisites:
- ✅ Microsoft 365/Teams account
- ✅ Azure subscription (free tier works)
- ✅ API Gateway deployed (what we're doing now)

---

## 📋 **Step-by-Step: Deploy Teams Bot**

### **Step 1: Register Bot in Azure Portal (15 min)**

1. **Go to Azure Portal**
   ```
   https://portal.azure.com
   ```

2. **Create Azure Bot Resource**
   - Search for "Azure Bot"
   - Click "Create"
   - Fill details:
     - **Bot handle**: `fileferry-bot` (unique name)
     - **Subscription**: Your subscription
     - **Resource group**: Create new or use existing
     - **Pricing tier**: F0 (Free)
     - **Microsoft App ID**: Create new
     - **Type of App**: Multi Tenant
   - Click "Review + create"

3. **Get Bot Credentials**
   After creation:
   - Go to "Configuration" blade
   - Copy **Microsoft App ID**
   - Click "Manage" next to Microsoft App ID
   - Create new client secret
   - Copy **Client Secret Value** (you'll need this!)

### **Step 2: Configure Messaging Endpoint (5 min)**

1. **In Azure Bot Configuration**
   - Messaging endpoint: `https://YOUR-API-GATEWAY-URL/prod/api/messages`
   - (We'll create this endpoint after API Gateway deployment)

2. **Save configuration**

### **Step 3: Add Teams Channel (2 min)**

1. **In Azure Bot**
   - Go to "Channels" blade
   - Click "Microsoft Teams" icon
   - Accept terms
   - Click "Apply"

2. **Get Teams App Link**
   - Click "Open in Teams" or copy the manifest link
   - Share this with users to install the bot

### **Step 4: Update Your Code (10 min)**

You already have the bot code in `MSteamsbot.py`! Just need to configure it.

**Create bot configuration file:**

```python
# config/teams_bot_config.json
{
  "microsoft_app_id": "YOUR-APP-ID-FROM-AZURE",
  "microsoft_app_password": "YOUR-CLIENT-SECRET",
  "api_gateway_url": "https://YOUR-API-GATEWAY-URL/prod"
}
```

### **Step 5: Deploy Bot Handler Lambda (5 min)**

Create a new Lambda function that handles Teams bot messages:

```bash
# In AWS CloudShell

# Create bot handler Lambda
cd ~/fileferry-deployment

cat > bot_handler.py << 'EOF'
import json
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from MSteamsbot import FileFerryTeamsBot

# Bot adapter settings
settings = BotFrameworkAdapterSettings(
    app_id=os.environ['MICROSOFT_APP_ID'],
    app_password=os.environ['MICROSOFT_APP_PASSWORD']
)
adapter = BotFrameworkAdapter(settings)
bot = FileFerryTeamsBot(config)

def lambda_handler(event, context):
    """Handle Teams bot messages"""
    try:
        body = json.loads(event['body'])
        
        # Process bot message
        async def process():
            await adapter.process_activity(body, auth_header, bot.on_turn)
        
        import asyncio
        asyncio.run(process())
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'success'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
EOF

# Create deployment package
mkdir -p bot_package
cp bot_handler.py bot_package/
cp -r ../MSteamsbot.py bot_package/
pip install botbuilder-core -t bot_package/
cd bot_package && zip -r ../bot_handler.zip . && cd ..

# Create Lambda function
aws lambda create-function \
  --function-name FileFerry-Teams-Bot-Handler \
  --runtime python3.11 \
  --role arn:aws:iam::637423332185:role/FileFerryLambdaExecutionRole \
  --handler bot_handler.lambda_handler \
  --zip-file fileb://bot_handler.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{MICROSOFT_APP_ID=YOUR-APP-ID,MICROSOFT_APP_PASSWORD=YOUR-SECRET,API_GATEWAY_URL=YOUR-API-URL}"
```

### **Step 6: Add API Gateway Endpoint for Bot (5 min)**

Add `/api/messages` endpoint to your API Gateway:

```bash
# In AWS CloudShell
API_ID="YOUR-API-GATEWAY-ID"

# Create /api resource
API_RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id ${API_ID} \
  --parent-id ${ROOT_ID} \
  --path-part "api" \
  --query 'id' \
  --output text)

# Create /api/messages resource
MESSAGES_RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id ${API_ID} \
  --parent-id ${API_RESOURCE_ID} \
  --path-part "messages" \
  --query 'id' \
  --output text)

# Create POST method
aws apigateway put-method \
  --rest-api-id ${API_ID} \
  --resource-id ${MESSAGES_RESOURCE_ID} \
  --http-method POST \
  --authorization-type NONE

# Integrate with Lambda
aws apigateway put-integration \
  --rest-api-id ${API_ID} \
  --resource-id ${MESSAGES_RESOURCE_ID} \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:637423332185:function:FileFerry-Teams-Bot-Handler/invocations"

# Add Lambda permission
aws lambda add-permission \
  --function-name FileFerry-Teams-Bot-Handler \
  --statement-id apigateway-teams-bot \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:637423332185:${API_ID}/*/POST/api/messages"

# Redeploy API
aws apigateway create-deployment \
  --rest-api-id ${API_ID} \
  --stage-name prod
```

### **Step 7: Test Your Bot (3 min)**

1. **Open Microsoft Teams**
2. **Click "Apps" in left sidebar**
3. **Search for "FileFerry"** or use the bot link from Azure
4. **Click "Add"**
5. **Start chatting!**

**Example conversation:**
```
You: Hi FileFerry, transfer file from S3 to FTP

Bot: 👋 Hello! I'd be happy to help you transfer a file.
     To proceed, I need:
     • S3 bucket name
     • S3 file path
     • FTP server details
     
     Could you provide these details?

You: S3 bucket is my-bucket, file is files/report.pdf, 
     FTP is ftp.company.com, user is admin, password is secret123

Bot: ✅ Got it! Starting file transfer...
     
     [Shows Adaptive Card with progress]
     
     Transfer ID: req_12345
     Status: In Progress
     [Progress bar: ████████░░ 80%]
     
Bot: 🎉 Transfer complete!
     File: report.pdf (2.5 MB)
     Transferred to: ftp.company.com/uploads/
     Duration: 45 seconds
```

---

## 🎯 **Option 2: Teams via Developer Portal (Quick Demo)**

### What You Get:
- Quick deployment for testing
- No Azure subscription needed
- Limited to your organization
- Good for proof-of-concept

### Time Required: **10 minutes**

### Steps:

1. **Go to Teams Developer Portal**
   ```
   https://dev.teams.microsoft.com/apps
   ```

2. **Create New App**
   - Click "New app"
   - App name: FileFerry Bot
   - Short description: File transfer automation
   - Full description: AI-powered file transfer between S3 and FTP

3. **Configure Bot**
   - Go to "App features" → "Bot"
   - Click "Create bot"
   - Bot name: FileFerry
   - Endpoint address: `https://YOUR-API-GATEWAY-URL/prod/api/messages`

4. **Set Bot Capabilities**
   - ✅ Personal chat
   - ✅ Team chat
   - ✅ Group chat

5. **Publish to Your Org**
   - Click "Publish"
   - Choose "Publish to your org"
   - Wait for admin approval (if required)

6. **Install in Teams**
   - Search "FileFerry" in Teams Apps
   - Click "Add"
   - Start chatting!

---

## 📊 **Comparison: Which Option to Choose?**

| Feature | Azure Bot Service | Developer Portal |
|---------|-------------------|------------------|
| **Time to Deploy** | 35-45 min | 10 min |
| **Cost** | Free tier available | Free |
| **Azure Subscription** | Required | Not required |
| **Production Ready** | ✅ Yes | ⚠️ Demo only |
| **Scale** | Unlimited | Limited |
| **Custom Features** | Full control | Limited |
| **Best For** | Production use | Quick demo/POC |

---

## 🚀 **Recommended Approach:**

### **For Now (Quick Demo):**
1. ✅ Deploy API Gateway (current task)
2. ✅ Use demo.html frontend (already exists)
3. ✅ Get system working end-to-end
4. 🔜 Add Teams bot later (10 min via Developer Portal)

### **For Production:**
1. ✅ Complete API Gateway + frontend
2. ✅ Test thoroughly
3. 🔜 Deploy Azure Bot Service (35 min)
4. 🔜 Publish to organization

---

## 💡 **How Teams Bot Works with Your System:**

```
User in Teams → "Transfer file from S3 to FTP"
           ↓
    Teams sends message to Azure Bot
           ↓
    Azure Bot → API Gateway /api/messages
           ↓
    Lambda: FileFerry-Teams-Bot-Handler
           ↓
    MSteamsbot.py processes message
           ↓
    Calls: API Gateway /transfer/start
           ↓
    Step Functions workflow starts
           ↓
    Bot sends Adaptive Card with progress
           ↓
    User sees: "✅ Transfer complete!"
```

---

## 📝 **Sample Adaptive Card (What Users See):**

```json
{
  "type": "AdaptiveCard",
  "version": "1.4",
  "body": [
    {
      "type": "TextBlock",
      "text": "🚀 File Transfer Started",
      "weight": "bolder",
      "size": "large"
    },
    {
      "type": "FactSet",
      "facts": [
        {
          "title": "Transfer ID:",
          "value": "req_12345"
        },
        {
          "title": "File:",
          "value": "report.pdf (2.5 MB)"
        },
        {
          "title": "Source:",
          "value": "S3: my-bucket/files/"
        },
        {
          "title": "Destination:",
          "value": "FTP: ftp.company.com"
        },
        {
          "title": "Status:",
          "value": "✅ Completed"
        }
      ]
    }
  ],
  "actions": [
    {
      "type": "Action.OpenUrl",
      "title": "View Details",
      "url": "https://fileferry.example.com/transfer/req_12345"
    }
  ]
}
```

---

## 🔧 **Troubleshooting:**

### Issue: "Bot not responding"
**Fix:** Check CloudWatch logs for Lambda: FileFerry-Teams-Bot-Handler

### Issue: "401 Unauthorized"
**Fix:** Verify Microsoft App ID and Password are correct in Lambda environment variables

### Issue: "Cannot find bot"
**Fix:** Ensure bot is published and added to your Teams org

### Issue: "Endpoint not responding"
**Fix:** Verify API Gateway endpoint `/api/messages` exists and is deployed

---

## ✅ **Quick Decision Guide:**

**Choose Developer Portal (10 min) if:**
- ✅ Just want to demo/test
- ✅ No Azure subscription
- ✅ Quick proof-of-concept
- ✅ Internal use only

**Choose Azure Bot Service (35 min) if:**
- ✅ Production deployment
- ✅ Need advanced features
- ✅ Want full control
- ✅ Multi-tenant support needed

---

## 🎯 **My Recommendation for You:**

### **Phase 1: NOW (Next 20 minutes)**
1. Complete API Gateway deployment ✅
2. Test with demo.html ✅
3. Verify end-to-end workflow ✅

### **Phase 2: LATER (Optional - 10 minutes)**
4. Add Teams bot via Developer Portal 🔜
5. Test bot in Teams 🔜

**Reason:** Get the core system working first (API Gateway + frontend), then add Teams bot as an enhancement. Teams bot is just another frontend - the backend (API Gateway, Lambda, Step Functions) works the same!

---

## 📞 **Want to Add Teams Bot Now?**

If you want to add Teams bot integration right after API Gateway:

1. I'll help you create the bot handler Lambda
2. Add `/api/messages` endpoint to API Gateway
3. Set up bot in Teams Developer Portal
4. Test bot conversation

**Total additional time: 15 minutes on top of API Gateway deployment**

---

## 🎉 **Summary:**

**YES!** You can absolutely use Microsoft Teams bot with FileFerry using the Developer Portal link method (quickest) or Azure Bot Service (full-featured).

**Current Priority:** 
1. Deploy API Gateway first (10-30 min) ← We're here
2. Test with demo.html
3. Then add Teams bot if desired (10-35 min)

**Ready to proceed with API Gateway deployment first, then add Teams bot?** 🚀
