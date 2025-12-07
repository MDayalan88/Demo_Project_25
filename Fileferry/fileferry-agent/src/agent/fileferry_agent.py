"""
FileFerry AI Agent - Main Orchestrator
Automates S3 to FTP/SFTP file transfers with ServiceNow integration
"""

from typing import Dict, Any, List
import asyncio
from datetime import datetime
import logging

# Agent Framework imports (requires: pip install agent-framework-azure-ai --pre)
from azure.ai.agents import Agent, AgentExecutor
from azure.ai.agents.models import AgentMessage, AgentResponse

from ..services.servicenow_service import ServiceNowService
from ..services.transfer_service import TransferService
from ..services.notification_service import NotificationService
from ..services.monitoring_service import MonitoringService
from ..handlers.sso_handler import SSOHandler
from ..handlers.s3_handler import S3Handler
from ..handlers.sftp_handler import SFTPHandler
from ..handlers.ftp_handler import FTPHandler
from ..models.transfer_job import TransferJob
from ..utils.logger import get_logger

logger = get_logger(__name__)


class FileFerryAgent:
    """
    AI-powered agent that orchestrates automated file transfers from S3 to FTP/SFTP servers
    with ServiceNow ticketing, SSO authentication, and monitoring capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the FileFerry Agent with all required services
        
        Args:
            config: Configuration dictionary containing all service settings
        """
        self.config = config
        
        # Initialize services
        self.servicenow = ServiceNowService(config.get('serviceNow', {}))
        self.sso_handler = SSOHandler(config.get('aws', {}).get('sso', {}))
        self.s3_handler = S3Handler(config.get('aws', {}).get('s3', {}))
        self.sftp_handler = SFTPHandler(config.get('sftp', {}))
        self.ftp_handler = FTPHandler(config.get('ftp', {}))
        self.monitoring = MonitoringService(config.get('monitoring', {}))
        self.notification = NotificationService(config.get('notification', {}))
        self.transfer_service = TransferService(
            transfer_handler=None,  # Will be set dynamically
            notification_service=self.notification,
            monitoring_service=self.monitoring
        )
        
        # Session management
        self.sso_session = None
        self.session_start_time = None
        self.session_timeout = 10  # 10 seconds as per requirement
        
        logger.info("FileFerry Agent initialized successfully")
    
    async def process_transfer_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: Process a complete file transfer request
        
        Args:
            request_data: Dictionary containing:
                - environment: Target environment (dev/staging/prod)
                - bucket_name: S3 bucket name
                - region: AWS region
                - assignment_group: ServiceNow assignment group
                - file_name: File to transfer
                - destination_type: 'sftp' or 'ftp'
                - destination_host: Target server hostname
                - user_email: Requestor email
                
        Returns:
            Dictionary with transfer results and ticket information
        """
        logger.info(f"Processing transfer request: {request_data.get('file_name')}")
        
        try:
            # Step 1: Validate request
            self._validate_request(request_data)
            
            # Step 2: Create ServiceNow tickets
            tickets = await self._create_servicenow_tickets(request_data)
            logger.info(f"ServiceNow tickets created: User={tickets['user_ticket']}, Assignment={tickets['assignment_ticket']}")
            
            # Step 3: Authenticate with SSO
            await self._authenticate_sso(request_data)
            
            # Step 4: List and verify file in S3
            file_metadata = await self._verify_s3_file(
                request_data['bucket_name'],
                request_data['region'],
                request_data['file_name']
            )
            
            # Step 5: Initiate file transfer
            transfer_job = await self._initiate_transfer(request_data, file_metadata, tickets)
            
            # Step 6: Auto-logout after 10 seconds
            await self._schedule_auto_logout()
            
            # Step 7: Monitor transfer (async)
            asyncio.create_task(self._monitor_and_notify(transfer_job, tickets))
            
            return {
                'status': 'success',
                'message': 'Transfer initiated successfully',
                'user_ticket': tickets['user_ticket'],
                'assignment_ticket': tickets['assignment_ticket'],
                'transfer_id': transfer_job.job_id,
                'file_name': request_data['file_name'],
                'file_size': file_metadata.get('size'),
                'estimated_time': self._estimate_transfer_time(file_metadata.get('size', 0))
            }
            
        except Exception as e:
            logger.error(f"Transfer request failed: {str(e)}", exc_info=True)
            await self.monitoring.track_error('transfer_request_failed', str(e))
            raise
    
    def _validate_request(self, request_data: Dict[str, Any]) -> None:
        """Validate that all mandatory fields are provided"""
        required_fields = [
            'environment', 'bucket_name', 'region', 
            'assignment_group', 'file_name', 'destination_type'
        ]
        
        missing = [field for field in required_fields if not request_data.get(field)]
        if missing:
            raise ValueError(f"Missing mandatory fields: {', '.join(missing)}")
        
        # Validate destination type
        if request_data['destination_type'] not in ['sftp', 'ftp']:
            raise ValueError("destination_type must be 'sftp' or 'ftp'")
        
        logger.info("Request validation passed")
    
    async def _create_servicenow_tickets(self, request_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Create two ServiceNow tickets: one for user, one for assignment team
        
        Returns:
            Dictionary with user_ticket and assignment_ticket IDs
        """
        timestamp = datetime.utcnow().isoformat()
        
        # User-facing ticket
        user_ticket_data = {
            'short_description': f"File Transfer Request: {request_data['file_name']}",
            'description': f"""
Automated File Transfer Request
================================
File: {request_data['file_name']}
Source: S3 Bucket {request_data['bucket_name']} ({request_data['region']})
Destination: {request_data['destination_type'].upper()} Server
Environment: {request_data['environment']}
Requested by: {request_data.get('user_email', 'Unknown')}
Request Time: {timestamp}

Status: Transfer initiated automatically via FileFerry Agent
            """,
            'category': 'File Transfer',
            'priority': 'Medium',
            'assignment_group': request_data['assignment_group']
        }
        
        user_ticket = await self.servicenow.create_ticket(user_ticket_data, ticket_type='user')
        
        # Assignment team audit ticket
        assignment_ticket_data = {
            'short_description': f"[AUDIT] File Transfer: {request_data['file_name']}",
            'description': f"""
Automated File Transfer - Assignment Team Audit
================================================
File: {request_data['file_name']}
Source: S3 Bucket {request_data['bucket_name']} ({request_data['region']})
Destination: {request_data['destination_type'].upper()} Server
Environment: {request_data['environment']}
User Ticket: {user_ticket}
Request Time: {timestamp}

This is an automated audit record for tracking purposes.
The file transfer is being processed automatically.
            """,
            'category': 'Audit',
            'priority': 'Low',
            'assignment_group': request_data['assignment_group']
        }
        
        assignment_ticket = await self.servicenow.create_ticket(assignment_ticket_data, ticket_type='assignment')
        
        # Track in monitoring
        await self.monitoring.track_metric('servicenow_tickets_created', 2, {
            'user_ticket': user_ticket,
            'assignment_ticket': assignment_ticket
        })
        
        return {
            'user_ticket': user_ticket,
            'assignment_ticket': assignment_ticket
        }
    
    async def _authenticate_sso(self, request_data: Dict[str, Any]) -> None:
        """Authenticate with AWS SSO and establish session"""
        logger.info("Initiating SSO authentication")
        
        self.sso_session = await self.sso_handler.authenticate(
            region=request_data['region']
        )
        self.session_start_time = datetime.utcnow()
        
        await self.monitoring.track_metric('sso_login_success', 1)
        logger.info("SSO authentication successful")
    
    async def _verify_s3_file(self, bucket_name: str, region: str, file_name: str) -> Dict[str, Any]:
        """
        Verify file exists in S3 and retrieve metadata
        User has read-only access as per security requirements
        """
        logger.info(f"Verifying file in S3: {bucket_name}/{file_name}")
        
        # List files in bucket (read-only operation)
        files = await self.s3_handler.list_files(bucket_name, region, prefix=file_name)
        
        if not files or file_name not in [f['key'] for f in files]:
            raise FileNotFoundError(f"File {file_name} not found in bucket {bucket_name}")
        
        # Get file metadata
        metadata = await self.s3_handler.get_file_metadata(bucket_name, file_name, region)
        
        logger.info(f"File verified: {metadata.get('size')} bytes, Last Modified: {metadata.get('last_modified')}")
        
        return metadata
    
    async def _initiate_transfer(
        self, 
        request_data: Dict[str, Any], 
        file_metadata: Dict[str, Any],
        tickets: Dict[str, str]
    ) -> TransferJob:
        """Initiate the file transfer from S3 to FTP/SFTP"""
        
        # Create transfer job
        transfer_job = TransferJob(
            source_type='s3',
            source_bucket=request_data['bucket_name'],
            source_key=request_data['file_name'],
            source_region=request_data['region'],
            destination_type=request_data['destination_type'],
            destination_host=request_data.get('destination_host'),
            file_size=file_metadata.get('size', 0),
            user_ticket=tickets['user_ticket'],
            assignment_ticket=tickets['assignment_ticket'],
            user_email=request_data.get('user_email')
        )
        
        # Select appropriate handler
        if request_data['destination_type'] == 'sftp':
            transfer_handler = self.sftp_handler
        else:
            transfer_handler = self.ftp_handler
        
        # Set handler in transfer service
        self.transfer_service.transfer_handler = transfer_handler
        
        # Start transfer asynchronously
        logger.info(f"Starting transfer: {transfer_job.job_id}")
        await self.transfer_service.start_transfer_async(transfer_job, self.s3_handler)
        
        await self.monitoring.track_metric('transfer_initiated', 1, {
            'job_id': transfer_job.job_id,
            'file_size': file_metadata.get('size', 0)
        })
        
        return transfer_job
    
    async def _schedule_auto_logout(self) -> None:
        """Auto-logout after 10 seconds as per security requirement"""
        await asyncio.sleep(self.session_timeout)
        
        if self.sso_session:
            await self.sso_handler.logout(self.sso_session)
            logger.info("SSO session automatically logged out after 10 seconds")
            self.sso_session = None
            await self.monitoring.track_metric('sso_auto_logout', 1)
    
    async def _monitor_and_notify(self, transfer_job: TransferJob, tickets: Dict[str, str]) -> None:
        """Monitor transfer progress and send notifications upon completion"""
        
        while transfer_job.status not in ['completed', 'failed']:
            await asyncio.sleep(5)  # Check every 5 seconds
            
            # Update progress in Datadog
            await self.monitoring.track_transfer_progress(transfer_job)
        
        # Transfer completed or failed
        if transfer_job.status == 'completed':
            message = f"""
✅ File Transfer Completed Successfully!

File: {transfer_job.source_key}
Size: {self._format_size(transfer_job.file_size)}
Duration: {transfer_job.duration} seconds
User Ticket: {tickets['user_ticket']}
Assignment Ticket: {tickets['assignment_ticket']}

Your file has been successfully transferred to the destination server.
            """
            await self.notification.send_teams_notification(message, transfer_job)
            await self.servicenow.update_ticket(tickets['user_ticket'], 'Resolved', 'Transfer completed successfully')
            
        else:
            message = f"""
❌ File Transfer Failed

File: {transfer_job.source_key}
Error: {transfer_job.error_message}
User Ticket: {tickets['user_ticket']}

Please contact support for assistance.
            """
            await self.notification.send_teams_notification(message, transfer_job)
            await self.servicenow.update_ticket(tickets['user_ticket'], 'Failed', f'Transfer failed: {transfer_job.error_message}')
        
        # Update assignment ticket
        await self.servicenow.update_ticket(
            tickets['assignment_ticket'], 
            transfer_job.status.capitalize(),
            f"Automated transfer {transfer_job.status}"
        )
    
    def _estimate_transfer_time(self, file_size: int) -> str:
        """Estimate transfer time based on file size"""
        # Assuming average speed of 10 MB/s
        seconds = file_size / (10 * 1024 * 1024)
        
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            return f"{int(seconds / 60)} minutes"
        else:
            return f"{int(seconds / 3600)} hours"
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"


# Agent Tools/Functions for AI decision-making
async def analyze_transfer_requirements(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    AI-powered analysis of transfer requirements
    Helps the agent make intelligent decisions about transfer optimization
    """
    file_size = request_data.get('file_size', 0)
    destination = request_data.get('destination_type', 'sftp')
    
    recommendations = {
        'compression_recommended': file_size > 100 * 1024 * 1024,  # > 100MB
        'chunk_transfer': file_size > 1024 * 1024 * 1024,  # > 1GB
        'preferred_protocol': 'sftp' if file_size > 500 * 1024 * 1024 else destination,
        'estimated_bandwidth': '10-50 MB/s',
        'security_level': 'high'
    }
    
    return recommendations
