"""
FastAPI Web Interface for FileFerry Agent
Provides REST API and web UI for users to initiate file transfers
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime
import uvicorn

from ..agent.fileferry_agent import FileFerryAgent
from ..utils.config_loader import load_config
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FileFerry Agent API",
    description="Automated S3 to FTP/SFTP file transfer service",
    version="1.0.0"
)

# Load configuration
config = load_config()
agent = FileFerryAgent(config)

# Request/Response Models
class TransferRequest(BaseModel):
    """File transfer request model"""
    environment: str = Field(..., description="Target environment (dev/staging/prod)")
    bucket_name: str = Field(..., description="S3 bucket name")
    region: str = Field(..., description="AWS region")
    assignment_group: str = Field(..., description="ServiceNow assignment group")
    file_name: str = Field(..., description="File name to transfer")
    destination_type: str = Field(..., description="Destination type: sftp or ftp")
    destination_host: Optional[str] = Field(None, description="Destination server hostname")
    user_email: str = Field(..., description="Requestor email address")
    
    @validator('destination_type')
    def validate_destination_type(cls, v):
        if v not in ['sftp', 'ftp']:
            raise ValueError('destination_type must be sftp or ftp')
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        if v not in ['dev', 'staging', 'prod']:
            raise ValueError('environment must be dev, staging, or prod')
        return v


class TransferResponse(BaseModel):
    """Transfer response model"""
    status: str
    message: str
    user_ticket: str
    assignment_ticket: str
    transfer_id: str
    file_name: str
    file_size: Optional[int] = None
    estimated_time: Optional[str] = None


class TransferStatus(BaseModel):
    """Transfer status model"""
    transfer_id: str
    status: str
    progress: Optional[float] = None
    error_message: Optional[str] = None


# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - returns simple web UI"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FileFerry Agent</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: #34495e;
            }
            input, select {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            button {
                background-color: #3498db;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 20px;
            }
            button:hover {
                background-color: #2980b9;
            }
            .result {
                margin-top: 20px;
                padding: 15px;
                border-radius: 5px;
                display: none;
            }
            .success {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
            }
            .error {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
            }
            .required {
                color: red;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚢 FileFerry Agent</h1>
            <p>Automated S3 to FTP/SFTP File Transfer Service</p>
            
            <form id="transferForm">
                <div class="form-group">
                    <label>Environment <span class="required">*</span></label>
                    <select id="environment" required>
                        <option value="">Select environment...</option>
                        <option value="dev">Development</option>
                        <option value="staging">Staging</option>
                        <option value="prod">Production</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>S3 Bucket Name <span class="required">*</span></label>
                    <input type="text" id="bucket_name" placeholder="my-s3-bucket" required>
                </div>
                
                <div class="form-group">
                    <label>AWS Region <span class="required">*</span></label>
                    <input type="text" id="region" placeholder="us-east-1" required>
                </div>
                
                <div class="form-group">
                    <label>Assignment Group <span class="required">*</span></label>
                    <input type="text" id="assignment_group" placeholder="IT-Operations" required>
                </div>
                
                <div class="form-group">
                    <label>File Name <span class="required">*</span></label>
                    <input type="text" id="file_name" placeholder="data/file.csv" required>
                </div>
                
                <div class="form-group">
                    <label>Destination Type <span class="required">*</span></label>
                    <select id="destination_type" required>
                        <option value="">Select destination...</option>
                        <option value="sftp">SFTP</option>
                        <option value="ftp">FTP</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Destination Host</label>
                    <input type="text" id="destination_host" placeholder="ftp.example.com">
                </div>
                
                <div class="form-group">
                    <label>Your Email <span class="required">*</span></label>
                    <input type="email" id="user_email" placeholder="user@example.com" required>
                </div>
                
                <button type="submit">Start Transfer</button>
            </form>
            
            <div id="result" class="result"></div>
        </div>
        
        <script>
            document.getElementById('transferForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = {
                    environment: document.getElementById('environment').value,
                    bucket_name: document.getElementById('bucket_name').value,
                    region: document.getElementById('region').value,
                    assignment_group: document.getElementById('assignment_group').value,
                    file_name: document.getElementById('file_name').value,
                    destination_type: document.getElementById('destination_type').value,
                    destination_host: document.getElementById('destination_host').value,
                    user_email: document.getElementById('user_email').value
                };
                
                try {
                    const response = await fetch('/api/transfer', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(formData)
                    });
                    
                    const result = await response.json();
                    const resultDiv = document.getElementById('result');
                    
                    if (response.ok) {
                        resultDiv.className = 'result success';
                        resultDiv.innerHTML = `
                            <h3>✅ Transfer Initiated Successfully!</h3>
                            <p><strong>User Ticket:</strong> ${result.user_ticket}</p>
                            <p><strong>Assignment Ticket:</strong> ${result.assignment_ticket}</p>
                            <p><strong>Transfer ID:</strong> ${result.transfer_id}</p>
                            <p><strong>File:</strong> ${result.file_name}</p>
                            <p><strong>Estimated Time:</strong> ${result.estimated_time}</p>
                            <p>You will receive a Microsoft Teams notification when the transfer completes.</p>
                        `;
                    } else {
                        resultDiv.className = 'result error';
                        resultDiv.innerHTML = `
                            <h3>❌ Transfer Failed</h3>
                            <p>${result.detail || 'An error occurred'}</p>
                        `;
                    }
                    
                    resultDiv.style.display = 'block';
                    
                } catch (error) {
                    const resultDiv = document.getElementById('result');
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = `
                        <h3>❌ Error</h3>
                        <p>${error.message}</p>
                    `;
                    resultDiv.style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/api/transfer", response_model=TransferResponse)
async def create_transfer(
    request: TransferRequest,
    background_tasks: BackgroundTasks
) -> TransferResponse:
    """
    Create a new file transfer request
    
    This endpoint:
    1. Validates the request
    2. Creates ServiceNow tickets
    3. Authenticates with SSO
    4. Initiates the file transfer
    5. Returns transfer details
    """
    try:
        logger.info(f"Received transfer request for file: {request.file_name}")
        
        # Convert request to dict
        request_data = request.dict()
        
        # Process transfer request
        result = await agent.process_transfer_request(request_data)
        
        return TransferResponse(**result)
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Transfer request failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/transfer/{transfer_id}", response_model=TransferStatus)
async def get_transfer_status(transfer_id: str) -> TransferStatus:
    """
    Get the status of a transfer by ID
    """
    # TODO: Implement transfer status tracking
    return TransferStatus(
        transfer_id=transfer_id,
        status="in_progress",
        progress=50.0
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "fileferry-agent",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/config")
async def get_config():
    """Get available configuration options (sanitized)"""
    return {
        "available_regions": ["us-east-1", "us-west-2", "eu-west-1"],
        "destination_types": ["sftp", "ftp"],
        "environments": ["dev", "staging", "prod"]
    }


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "api.web_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
