"""
Slack Backend Handler - Replaces Teams Bot
Handles Slack events, commands, and provides REST API for React frontend
"""

from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from src.ai_agent.bedrock_agent import BedrockFileFerryAgent
    from src.utils.logger import get_logger
    from src.utils.config import load_config
    logger = get_logger(__name__)
except ImportError as e:
    print(f"⚠️  Warning: Could not import FileFerry modules: {e}")
    print("Running in standalone mode with mock responses")
    logger = None
    BedrockFileFerryAgent = None

# Initialize FastAPI app
app = FastAPI(title="FileFerry Slack API")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load config and initialize agent
try:
    config = load_config('config/config.yaml')
    bedrock_agent = BedrockFileFerryAgent(config)
    if logger:
        logger.info("✅ Slack Backend API initialized")
    print("✅ Slack Backend API initialized with FileFerry agent")
except Exception as e:
    print(f"⚠️  Running in demo mode: {e}")
    config = None
    bedrock_agent = None


# Pydantic models for request/response
class ChatMessage(BaseModel):
    user_id: str
    message: str


class TransferRequest(BaseModel):
    user_id: str
    source_bucket: str
    source_key: str
    destination_type: str  # 'ftp' or 'sftp'
    destination_host: str
    destination_path: str
    destination_user: str
    destination_password: str
    priority: str = 'medium'


class S3ListRequest(BaseModel):
    user_id: str
    region: str = 'us-east-1'
    bucket_name: str = None


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "FileFerry Slack API",
        "version": "1.0.0"
    }


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # TODO: Implement actual stats from DynamoDB
        return {
            "total_transfers": 156,
            "success_rate": 98.5,
            "active_transfers": 2,
            "failed_transfers": 3
        }
    except Exception as e:
        if logger:
            logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/recent-transfers")
async def get_recent_transfers():
    """Get recent transfer activity"""
    try:
        # TODO: Implement actual transfers from DynamoDB
        return [
            {
                "id": "transfer_001",
                "file_name": "data_export_2025.csv",
                "source": "fileferry-bucket",
                "destination": "ftp.example.com",
                "status": "completed",
                "timestamp": "2025-12-03T10:30:00Z"
            },
            {
                "id": "transfer_002",
                "file_name": "report.pdf",
                "source": "reports-bucket",
                "destination": "sftp.partner.com",
                "status": "in_progress",
                "timestamp": "2025-12-03T11:00:00Z"
            }
        ]
    except Exception as e:
        logger.error(f"Error fetching recent transfers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/s3/list-buckets")
async def list_s3_buckets(request: S3ListRequest):
    """List S3 buckets using AI agent"""
    try:
        logger.info(f"Listing S3 buckets for user: {request.user_id}")
        
        # Use AI agent to list buckets
        result = await bedrock_agent.process_natural_language_request(
            user_id=request.user_id,
            user_message=f"List my S3 buckets in {request.region}"
        )
        
        # Extract buckets from response
        # TODO: Parse AI response or use tool results directly
        return {
            "success": True,
            "buckets": result.get('metadata', {}).get('tool_results', [])
        }
        
    except Exception as e:
        logger.error(f"Error listing S3 buckets: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/s3/list-contents")
async def list_bucket_contents(request: S3ListRequest):
    """List contents of an S3 bucket"""
    try:
        if not request.bucket_name:
            raise HTTPException(status_code=400, detail="bucket_name is required")
        
        logger.info(f"Listing contents of bucket: {request.bucket_name}")
        
        # Use AI agent to list bucket contents
        result = await bedrock_agent.process_natural_language_request(
            user_id=request.user_id,
            user_message=f"List contents of bucket {request.bucket_name}"
        )
        
        return {
            "success": True,
            "files": result.get('metadata', {}).get('tool_results', [])
        }
        
    except Exception as e:
        logger.error(f"Error listing bucket contents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/message")
async def chat_with_agent(message: ChatMessage):
    """Send message to AI agent and get response"""
    try:
        logger.info(f"Chat message from {message.user_id}: {message.message}")
        
        result = await bedrock_agent.process_natural_language_request(
            user_id=message.user_id,
            user_message=message.message
        )
        
        return {
            "success": result.get('success', False),
            "response": result.get('response', 'Sorry, I encountered an error.'),
            "metadata": result.get('metadata', {})
        }
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transfer/create")
async def create_transfer(transfer: TransferRequest):
    """Create a new file transfer request"""
    try:
        logger.info(f"Creating transfer request from {transfer.user_id}")
        
        # Build transfer message
        message = (
            f"Transfer file {transfer.source_key} from S3 bucket {transfer.source_bucket} "
            f"to {transfer.destination_type.upper()} server {transfer.destination_host}:{transfer.destination_path} "
            f"using credentials user={transfer.destination_user}. Priority: {transfer.priority}"
        )
        
        result = await bedrock_agent.process_natural_language_request(
            user_id=transfer.user_id,
            user_message=message
        )
        
        return {
            "success": result.get('success', False),
            "message": "Transfer request submitted successfully",
            "transfer_id": f"transfer_{int(asyncio.get_event_loop().time() * 1000)}",
            "response": result.get('response', '')
        }
        
    except Exception as e:
        logger.error(f"Error creating transfer: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transfer/history")
async def get_transfer_history(user_id: str):
    """Get transfer history for a user"""
    try:
        logger.info(f"Fetching transfer history for user: {user_id}")
        
        # TODO: Implement actual history from DynamoDB
        return [
            {
                "id": "transfer_001",
                "file_name": "data_export_2025.csv",
                "source_bucket": "fileferry-bucket",
                "destination": "ftp.example.com:/uploads/",
                "status": "completed",
                "started_at": "2025-12-03T10:00:00Z",
                "completed_at": "2025-12-03T10:05:00Z"
            },
            {
                "id": "transfer_002",
                "file_name": "large_file.zip",
                "source_bucket": "backup-bucket",
                "destination": "sftp.partner.com:/incoming/",
                "status": "in_progress",
                "started_at": "2025-12-03T11:00:00Z",
                "completed_at": None
            }
        ]
        
    except Exception as e:
        logger.error(f"Error fetching transfer history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
