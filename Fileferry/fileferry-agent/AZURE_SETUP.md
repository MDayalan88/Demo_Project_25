# Azure Blob Storage Integration Setup Guide

## 🎯 Overview

Your FileFerry Agent now supports **both AWS and Azure** storage! This guide will help you set up and test the Azure Blob Storage integration.

---

## 📋 Prerequisites

### 1. Install Required Packages

```powershell
# Navigate to project directory
cd c:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent

# Install Azure SDK packages
pip install azure-storage-blob==12.19.0 azure-identity==1.15.0 azure-core==1.29.5

# Or install all requirements
pip install -r requirements.txt
```

### 2. Install Azurite (Azure Storage Emulator)

**Option A: Using npm (Recommended)**
```powershell
# Install globally
npm install -g azurite

# Verify installation
azurite --version
```

**Option B: Using Docker**
```powershell
docker pull mcr.microsoft.com/azure-storage/azurite

# Run Azurite
docker run -p 10000:10000 -p 10001:10001 -p 10002:10002 mcr.microsoft.com/azure-storage/azurite
```

**Option C: Using Azure Storage Explorer**
- Download: https://azure.microsoft.com/features/storage-explorer/
- Includes built-in Azurite emulator

---

## 🚀 Quick Start (Local Development with Azurite)

### Step 1: Start Azurite Emulator

```powershell
# Start Azurite in the background
azurite --silent --location c:\azurite --debug c:\azurite\debug.log

# Or start with verbose output
azurite --location c:\azurite
```

**Azurite will start on:**
- Blob Service: `http://127.0.0.1:10000`
- Queue Service: `http://127.0.0.1:10001`
- Table Service: `http://127.0.0.1:10002`

### Step 2: Verify Configuration

Check `config/config.yaml` has Azure settings:

```yaml
# Azure Settings
azure:
  # Set use_emulator to true for local development with Azurite
  use_emulator: true
  
  # For production Azure (uncomment and configure):
  # use_emulator: false
  # connection_string: ${AZURE_STORAGE_CONNECTION_STRING}
  # account_name: ${AZURE_STORAGE_ACCOUNT_NAME}
  # account_url: https://<your-account>.blob.core.windows.net
```

### Step 3: Run Test Script

```powershell
# Run Azure integration tests
python test_azure_blob.py
```

**Expected Output:**
```
============================================================
Azure Blob Storage Integration Test
============================================================

✅ Step 1: Initializing Azure Blob Manager...
   ✓ Azure Blob Manager initialized (Azurite mode)

✅ Step 2: Creating test container...
   ✓ Container 'test-container' created

✅ Step 3: Listing containers...
   ✓ Found 1 container(s):
     - test-container

✅ Step 4: Uploading test blob...
   ✓ Blob 'test-file.txt' uploaded
     Size: 65 bytes
     ETag: 0x8DCB76D4A2E4F30

✅ Step 5: Listing blobs in container...
   ✓ Found 1 blob(s) in 'test-container':
     - test-file.txt (65 bytes)

✅ Step 6: Getting blob metadata...
   ✓ Metadata for 'test-file.txt':
     Size: 65 bytes
     Content-Type: text/plain
     Last Modified: 2025-12-07T...
     Custom Metadata: {'source': 'test_script', 'type': 'demo'}

✅ Step 7: Downloading blob...
   ✓ Downloaded 65 bytes
     Content: Hello from FileFerry Agent! Azure + AWS hybrid cloud integration.

✅ Step 8: Verifying data integrity...
   ✓ Data integrity verified - upload/download successful!

============================================================
✅ ALL TESTS PASSED!
============================================================
```

---

## 🔧 Configuration Options

### Local Development (Azurite)

```yaml
azure:
  use_emulator: true
  # No additional configuration needed
```

**Default Azurite Connection:**
- Account Name: `devstoreaccount1`
- Account Key: `Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==`
- Blob Endpoint: `http://127.0.0.1:10000/devstoreaccount1`

### Production Azure (Real Cloud)

```yaml
azure:
  use_emulator: false
  connection_string: "DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=mykey;EndpointSuffix=core.windows.net"
```

**Or using Managed Identity:**

```yaml
azure:
  use_emulator: false
  account_url: "https://mystorageaccount.blob.core.windows.net"
```

**Set environment variables:**

```powershell
# Windows PowerShell
$env:AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=..."
$env:AZURE_STORAGE_ACCOUNT_NAME="mystorageaccount"

# Or add to .env file
```

---

## 🧪 Testing with Agent

### Test Agent Integration

```python
from agent import AgentTools
import yaml
import asyncio

async def test_hybrid_agent():
    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize agent (supports both AWS and Azure)
    agent = AgentTools(config)
    
    # Test AWS S3
    aws_buckets = await agent.list_s3_buckets(user_id="test-user")
    print(f"AWS Buckets: {len(aws_buckets)}")
    
    # Test Azure Blob Storage
    azure_containers = await agent.list_azure_containers(user_id="test-user")
    print(f"Azure Containers: {len(azure_containers)}")
    
    # List blobs in Azure container
    if azure_containers:
        blobs = await agent.list_azure_blobs(
            user_id="test-user",
            container_name=azure_containers[0]['name']
        )
        print(f"Azure Blobs: {len(blobs)}")

asyncio.run(test_hybrid_agent())
```

---

## 📊 Architecture Overview

### Hybrid Cloud Support

```
Frontend (demo-hybrid.html)
    ↓
    ↓ [User selects AWS or Azure]
    ↓
AgentTools (agent.py)
    ↓
    ├─→ S3Manager (AWS) ──→ boto3 ──→ AWS S3
    │
    └─→ AzureBlobManager (Azure) ──→ azure-storage-blob ──→ Azure Blob Storage
                                                               or
                                                          Azurite Emulator
```

### Request-Level Isolation

Each request specifies cloud provider:
- **AWS Request**: Uses `s3_manager` → boto3 → AWS S3
- **Azure Request**: Uses `azure_blob_manager` → Azure SDK → Blob Storage

No conflicts, complete isolation!

---

## 🎯 API Equivalence

| Operation | AWS S3 | Azure Blob Storage |
|-----------|--------|-------------------|
| **Container** | Bucket | Container |
| **Object** | Object/Key | Blob |
| **List Containers** | `list_buckets()` | `list_containers()` |
| **List Objects** | `list_objects_v2()` | `list_blobs()` |
| **Upload** | `put_object()` | `upload_blob()` |
| **Download** | `get_object()` | `download_blob()` |
| **Metadata** | `head_object()` | `get_blob_properties()` |
| **Delete** | `delete_object()` | `delete_blob()` |

---

## 🔍 Troubleshooting

### Issue: "Connection refused" error

**Solution:**
```powershell
# Check if Azurite is running
Get-Process azurite

# If not running, start it:
azurite --silent --location c:\azurite
```

### Issue: "No module named 'azure'"

**Solution:**
```powershell
# Install Azure packages
pip install azure-storage-blob==12.19.0 azure-identity==1.15.0
```

### Issue: "Container already exists"

**Solution:**
```powershell
# This is OK! The test script handles this gracefully
# You can also reset Azurite:
Remove-Item c:\azurite\* -Recurse -Force
azurite --silent --location c:\azurite
```

### Issue: Test passes but frontend doesn't work

**Solution:**
Your frontend is already Azure-ready! You need to:
1. Create an API endpoint that calls `agent.list_azure_containers()`
2. Update `demo-hybrid.html` to call your API instead of using mock data

---

## 🎉 Production Deployment

### Switch to Real Azure

1. **Get Azure Storage Account credentials:**
   - Portal: https://portal.azure.com
   - Create Storage Account
   - Copy connection string

2. **Update `config/config.yaml`:**
   ```yaml
   azure:
     use_emulator: false
     connection_string: "<your-connection-string>"
   ```

3. **Test with real Azure:**
   ```powershell
   python test_azure_blob.py
   ```

### Free Azure Options

1. **Azure Free Tier:**
   - $200 credit for 30 days
   - 5GB Blob Storage always free
   - Sign up: https://azure.microsoft.com/free/

2. **Azure for Students:**
   - $100 credit (no credit card required)
   - Sign up: https://azure.microsoft.com/free/students/

---

## 📚 Additional Resources

- **Azure Blob Storage Docs:** https://learn.microsoft.com/azure/storage/blobs/
- **Azurite Emulator Docs:** https://learn.microsoft.com/azure/storage/common/storage-use-azurite
- **Python SDK Docs:** https://learn.microsoft.com/python/api/azure-storage-blob/
- **Storage Explorer:** https://azure.microsoft.com/features/storage-explorer/

---

## ✅ Next Steps

1. ✅ Azure SDK installed
2. ✅ Azurite running locally
3. ✅ Tests passing
4. 🔲 Connect frontend to backend API
5. 🔲 Deploy to production Azure
6. 🔲 Add Azure Cosmos DB (optional)
7. 🔲 Add Azure OpenAI (optional)

---

**🎉 Congratulations! Your agent now supports both AWS and Azure storage!**
