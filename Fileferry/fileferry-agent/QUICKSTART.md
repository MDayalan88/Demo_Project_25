# 🚀 FileFerry AI Agent - Quick Start Guide

## ⚡ 5-Minute Setup (Development)

### 1. Install Dependencies (1 min)
```bash
cd fileferry-agent
pip install boto3 pyyaml python-dotenv aiohttp aws-xray-sdk botbuilder-core
```

### 2. Set Environment Variables (1 min)
```bash
# Copy template
cp .env.example .env

# Edit .env with your AWS credentials
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### 3. Create DynamoDB Tables (2 min)
```bash
python infrastructure/create_dynamodb_tables.py us-east-1
```

### 4. Test Locally (1 min)
```python
# test_agent.py
import asyncio
from src.ai_agent.bedrock_agent import BedrockFileFerryAgent
from src.utils.config_loader import load_config

async def test():
    config = load_config('config/config.yaml')
    agent = BedrockFileFerryAgent(config)
    
    response = await agent.process_natural_language_request(
        user_id="test_user",
        user_message="List my S3 buckets in us-east-1"
    )
    
    print(response)

asyncio.run(test())
```

Run:
```bash
python test_agent.py
```

---

## 📝 Example Commands

Try these in Microsoft Teams (after deployment):

### Basic Operations
```
"Hello FileFerry"
"List my S3 buckets"
"Show files in bucket my-data-bucket"
"Get details for file data.csv in bucket my-data-bucket"
```

### File Transfers
```
"Transfer data.csv from my-bucket to SFTP server ftp.example.com"
"Move file report.pdf from bucket reports-bucket to FTP server 192.168.1.100"
"Copy all CSV files from bucket analytics to SFTP server secure.company.com"
```

### History & Status
```
"Show my transfer history"
"What's the status of my latest transfer?"
"Show me transfers from last week"
```

### Analysis
```
"Analyze transfer for large-file.zip in bucket big-data"
"What are the chances of success for this transfer?"
"Recommend strategy for 5GB file transfer"
```

---

## 🎯 Next Steps

1. **Deploy to AWS**: Follow [DEPLOYMENT.md](DEPLOYMENT.md)
2. **Register Teams Bot**: See Azure Bot Service setup
3. **Configure SSO**: Set up IAM Identity Center
4. **Train Users**: Share example commands
5. **Monitor**: Set up CloudWatch dashboards

---

## 📞 Get Help

- **Docs**: See README-AGENT.md
- **Deployment**: See DEPLOYMENT.md  
- **Issues**: Check troubleshooting section
- **Support**: Contact DevOps team

---

**Happy transferring! 🎉**
