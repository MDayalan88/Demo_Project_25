"""
Simple Slack Backend API - For Testing Frontend Without Full Agent Setup
Includes ServiceNow Integration
"""

from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import aiohttp
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="FileFerry Slack API (Demo Mode)")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ServiceNow Configuration
SERVICENOW_ENABLED = False
SERVICENOW_CONFIG = {
    "instance_url": os.getenv("SERVICENOW_INSTANCE_URL", "").rstrip('/'),
    "username": os.getenv("SERVICENOW_USERNAME", "admin"),
    "password": os.getenv("SERVICENOW_PASSWORD", "")
}

if SERVICENOW_CONFIG["instance_url"] and SERVICENOW_CONFIG["password"]:
    SERVICENOW_ENABLED = True
    print("✅ ServiceNow integration ENABLED")
    print(f"   Instance: {SERVICENOW_CONFIG['instance_url']}")
else:
    print("⚠️  ServiceNow integration DISABLED (credentials not found)")

print("✅ Slack Backend API initialized in DEMO MODE")
print("📝 This is a simplified version for testing the React frontend")


# Pydantic models
class ChatMessage(BaseModel):
    user_id: str
    message: str


class TransferRequest(BaseModel):
    user_id: str
    source_bucket: str
    source_key: str
    destination_type: str
    destination_host: str
    destination_path: str
    destination_user: str
    destination_password: str
    priority: Optional[str] = "medium"


class S3ListRequest(BaseModel):
    user_id: str
    bucket_name: Optional[str] = None
    region: Optional[str] = "us-east-1"


# Mock data
MOCK_TRANSFERS = [
    {
        "id": "transfer_001",
        "file_name": "data_export_2025.csv",
        "source": "fileferry-bucket",
        "destination": "ftp.example.com",
        "status": "completed",
        "timestamp": "2025-12-03T10:30:00Z",
        "size": "1.2 MB"
    },
    {
        "id": "transfer_002",
        "file_name": "report.pdf",
        "source": "documents-bucket",
        "destination": "sftp.partner.com",
        "status": "in_progress",
        "timestamp": "2025-12-03T11:00:00Z",
        "size": "450 KB"
    },
    {
        "id": "transfer_003",
        "file_name": "backup.zip",
        "source": "backup-bucket",
        "destination": "ftp.backup.com",
        "status": "failed",
        "timestamp": "2025-12-03T09:15:00Z",
        "size": "5.8 GB"
    }
]

MOCK_BUCKETS = [
    {
        "name": "fileferry-bucket",
        "region": "us-east-1",
        "creation_date": "2025-12-02T00:00:00Z"
    },
    {
        "name": "documents-bucket",
        "region": "us-east-1",
        "creation_date": "2025-11-15T00:00:00Z"
    }
]

MOCK_FILES = {
    "fileferry-bucket": [
        {
            "key": "data_export_2025.csv",
            "size": 1258291,
            "last_modified": "2025-12-02T14:30:00Z"
        },
        {
            "key": "report.pdf",
            "size": 460800,
            "last_modified": "2025-12-01T09:20:00Z"
        }
    ],
    "documents-bucket": [
        {
            "key": "invoice_123.pdf",
            "size": 125000,
            "last_modified": "2025-11-30T16:45:00Z"
        }
    ]
}


# ServiceNow Helper Functions
async def create_servicenow_ticket(transfer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a ticket in ServiceNow for file transfer"""
    if not SERVICENOW_ENABLED:
        print("⚠️  ServiceNow disabled, skipping ticket creation")
        return None
    
    url = f"{SERVICENOW_CONFIG['instance_url']}/api/now/table/incident"
    auth = aiohttp.BasicAuth(SERVICENOW_CONFIG['username'], SERVICENOW_CONFIG['password'])
    
    payload = {
        "short_description": f"FileFerry Transfer - {transfer_data.get('file_name', 'Unknown')}",
        "description": f"""File Transfer Request via FileFerry Agent

Source: {transfer_data.get('source', 'N/A')}
Destination: {transfer_data.get('destination', 'N/A')}
File: {transfer_data.get('file_name', 'N/A')}
User: {transfer_data.get('user_id', 'N/A')}
Priority: {transfer_data.get('priority', 'medium')}
Status: {transfer_data.get('status', 'pending')}
Timestamp: {transfer_data.get('timestamp', 'N/A')}

This ticket was automatically created by the FileFerry automation system.
""",
        "urgency": "2",  # Medium
        "impact": "2",   # Medium
        "assignment_group": "DataOps",
        "caller_id": SERVICENOW_CONFIG['username']
    }
    
    try:
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.post(url, json=payload) as response:
                if response.status == 201:
                    data = await response.json()
                    ticket = data.get('result', {})
                    print(f"✅ ServiceNow ticket created: {ticket.get('number')}")
                    return ticket
                else:
                    print(f"❌ Failed to create ServiceNow ticket: {response.status}")
                    return None
    except Exception as e:
        print(f"❌ ServiceNow error: {str(e)}")
        return None


# Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "FileFerry Slack API (Demo)",
        "version": "1.0.0",
        "mode": "demo",
        "servicenow_enabled": SERVICENOW_ENABLED
    }


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    return {
        "total_transfers": 156,
        "success_rate": 98.5,
        "active_transfers": 2,
        "failed_transfers": 3
    }


@app.get("/api/dashboard/recent-transfers")
async def get_recent_transfers():
    """Get recent transfer activity"""
    return MOCK_TRANSFERS[:5]


@app.post("/api/s3/list-buckets")
async def list_s3_buckets(request: S3ListRequest):
    """List S3 buckets"""
    print(f"📦 Listing S3 buckets for user: {request.user_id}")
    return {
        "success": True,
        "buckets": MOCK_BUCKETS
    }


@app.post("/api/s3/list-contents")
async def list_bucket_contents(request: S3ListRequest):
    """List contents of an S3 bucket"""
    if not request.bucket_name:
        raise HTTPException(status_code=400, detail="bucket_name is required")
    
    print(f"📁 Listing contents of bucket: {request.bucket_name}")
    
    files = MOCK_FILES.get(request.bucket_name, [])
    return {
        "success": True,
        "files": files
    }


@app.post("/api/chat/message")
async def chat_with_agent(message: ChatMessage):
    """Send message to AI agent and get response"""
    print(f"💬 Chat message from {message.user_id}: {message.message}")
    
    # Generate mock AI response based on message
    user_msg = message.message.lower()
    
    if "bucket" in user_msg and "list" in user_msg:
        response = f"I found {len(MOCK_BUCKETS)} S3 buckets in us-east-1:\n\n"
        for bucket in MOCK_BUCKETS:
            response += f"• {bucket['name']} (created {bucket['creation_date'][:10]})\n"
    elif "transfer" in user_msg:
        response = f"You have {len(MOCK_TRANSFERS)} recent transfers:\n\n"
        for transfer in MOCK_TRANSFERS[:3]:
            response += f"• {transfer['file_name']} - {transfer['status']}\n"
    elif "help" in user_msg:
        response = """I can help you with:
• List S3 buckets
• Browse bucket contents
• Create file transfers
• Check transfer status
• Monitor your file operations

Try asking: "List my S3 buckets" or "Show recent transfers"
"""
    else:
        response = f"I received your message: '{message.message}'\n\nThis is a demo response. In production, I would use AWS Bedrock Claude 3.5 Sonnet to process your request and interact with S3, FTP, and SFTP services."
    
    return {
        "success": True,
        "response": response,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/transfer/create")
async def create_transfer(request: TransferRequest):
    """Create a new file transfer"""
    print(f"🚀 Creating transfer for user: {request.user_id}")
    print(f"   Source: {request.source_bucket}/{request.source_key}")
    print(f"   Destination: {request.destination_type}://{request.destination_host}{request.destination_path}")
    
    new_transfer = {
        "id": f"transfer_{len(MOCK_TRANSFERS) + 1:03d}",
        "file_name": request.source_key,
        "source": request.source_bucket,
        "destination": f"{request.destination_type}://{request.destination_host}",
        "status": "pending",
        "timestamp": datetime.utcnow().isoformat(),
        "priority": request.priority,
        "user_id": request.user_id
    }
    
    MOCK_TRANSFERS.insert(0, new_transfer)
    
    # Create ServiceNow ticket if enabled
    servicenow_ticket = None
    if SERVICENOW_ENABLED:
        servicenow_ticket = await create_servicenow_ticket(new_transfer)
        if servicenow_ticket:
            new_transfer["servicenow_ticket"] = servicenow_ticket.get("number")
            new_transfer["servicenow_sys_id"] = servicenow_ticket.get("sys_id")
    
    return {
        "success": True,
        "transfer_id": new_transfer["id"],
        "message": "Transfer request created successfully",
        "transfer": new_transfer,
        "servicenow_ticket": servicenow_ticket.get("number") if servicenow_ticket else None
    }


@app.get("/api/transfer/history")
async def get_transfer_history(user_id: str):
    """Get transfer history for a user"""
    print(f"📜 Getting transfer history for user: {user_id}")
    return MOCK_TRANSFERS


@app.post("/api/transfer/initiate")
async def initiate_transfer(request: TransferRequest):
    """Initiate a file transfer immediately"""
    print(f"⚡ Initiating immediate transfer for user: {request.user_id}")
    
    return {
        "success": True,
        "message": "Transfer initiated",
        "status": "in_progress"
    }


# Run the application
if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting FileFerry Slack API (Demo Mode)...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
