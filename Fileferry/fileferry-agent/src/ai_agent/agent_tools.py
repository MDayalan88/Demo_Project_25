"""
AgentTools - Complete implementation of 9 tools for BedrockFileFerryAgent
Integrated architecture following the FileFerry AI Agent specification
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

# Import handlers
from src.storage.s3_manager import S3Manager
from src.storage.dynamodb_manager import DynamoDBManager
from src.handlers.transfer_handler import TransferHandler
from src.handlers.sso_handler import SSOHandler
from src.handlers.servicenow_handler import ServiceNowHandler

logger = logging.getLogger(__name__)


class AgentTools:
    """
    Complete tool implementations for FileFerry AI Agent.
    
    Provides 9 integrated tools as per architecture:
    1. list_s3_buckets() - List accessible S3 buckets in a region
    2. list_bucket_contents() - List files in a specific bucket
    3. get_file_metadata() - Get detailed file information (with 24hr cache)
    4. validate_user_access() - Verify user has read-only permissions
    5. analyze_transfer_request() - Analyze transfer requirements and strategy
    6. predict_transfer_outcome() - Predict success rate and duration using ML
    7. create_servicenow_tickets() - Create DUAL tickets (user + audit)
    8. execute_transfer() - Start AWS Step Functions transfer workflow
    9. get_transfer_history() - Retrieve user's past transfers
    
    All tools integrate with:
    - SSO Handler (10-second session timeout)
    - DynamoDB (5 tables: UserContext, TransferRequests, AgentLearning, S3FileCache, ActiveSessions)
    - Step Functions (transfer workflow orchestration)
    - ServiceNow API (dual ticket system)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize all handlers and managers.
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        
        logger.info("Initializing AgentTools with complete architecture...")
        
        # Initialize SSO Handler FIRST (required for authentication)
        self.sso_handler = SSOHandler(config)
        
        # Initialize storage managers
        self.s3_manager = S3Manager(config)
        self.dynamodb_manager = DynamoDBManager(config)
        
        # Initialize transfer handler (depends on SSO)
        self.transfer_handler = TransferHandler(config, self.sso_handler)
        
        # Initialize ServiceNow handler
        self.servicenow_handler = ServiceNowHandler(config)
        
        logger.info("✅ AgentTools initialized: All 9 tools ready with SSO, DynamoDB, S3, Step Functions, ServiceNow")
    
    # ========================================================================
    # TOOL 1: list_s3_buckets
    # ========================================================================
    
    def list_s3_buckets(self, region: str, session_token: str) -> Dict[str, Any]:
        """
        Tool 1: List all accessible S3 buckets in a specific AWS region.
        
        Requires active SSO session with 10-second timeout enforcement.
        Returns bucket list with names, creation dates, and regions.
        
        Args:
            region: AWS region (e.g., us-east-1, us-west-2)
            session_token: Active SSO session token
            
        Returns:
            {
                "success": True,
                "region": "us-east-1",
                "buckets": [...],
                "count": 5,
                "timestamp": "2025-12-03T..."
            }
        """
        try:
            logger.info(f"[TOOL1] list_s3_buckets: region={region}")
            
            # STEP 1: Validate SSO session (10-second timeout)
            if not self.sso_handler.is_session_valid(session_token):
                logger.warning(f"[TOOL1] SSO session expired or invalid")
                return {
                    "success": False,
                    "error": "SSO session expired or invalid. Please authenticate again with new ServiceNow request.",
                    "error_code": "SESSION_EXPIRED",
                    "timestamp": datetime.now().isoformat()
                }
            
            # STEP 2: Get temporary AWS credentials from SSO session
            credentials = self.sso_handler.get_session_credentials(session_token)
            if not credentials:
                return {
                    "success": False,
                    "error": "Failed to retrieve SSO credentials",
                    "error_code": "CREDENTIALS_ERROR"
                }
            
            # STEP 3: List buckets using S3Manager with SSO credentials
            buckets = self.s3_manager.list_buckets(region, credentials)
            
            logger.info(f"[TOOL1] Found {len(buckets)} buckets in {region}")
            
            return {
                "success": True,
                "region": region,
                "buckets": buckets,
                "count": len(buckets),
                "read_only_access": True,  # Always read-only per architecture
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[TOOL1] Error listing buckets: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "BUCKET_LIST_ERROR",
                "timestamp": datetime.now().isoformat()
            }
    
    # ========================================================================
    # TOOL 2: list_bucket_contents
    # ========================================================================
    
    def list_bucket_contents(
        self,
        bucket_name: str,
        session_token: str,
        prefix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tool 2: List files and folders in a specific S3 bucket.
        
        Shows file names, sizes, last modified dates, and storage classes.
        Supports folder prefix filtering for navigation.
        
        Args:
            bucket_name: Name of the S3 bucket
            session_token: Active SSO session token
            prefix: Optional folder prefix (e.g., "folder1/subfolder/")
            
        Returns:
            {
                "success": True,
                "bucket": "my-bucket",
                "prefix": "folder1/",
                "files": [
                    {
                        "key": "folder1/file.txt",
                        "size": 1024,
                        "last_modified": "2025-12-01T...",
                        "storage_class": "STANDARD"
                    }
                ],
                "count": 10
            }
        """
        try:
            logger.info(f"[TOOL2] list_bucket_contents: bucket={bucket_name}, prefix={prefix}")
            
            # Validate SSO session
            if not self.sso_handler.is_session_valid(session_token):
                return {
                    "success": False,
                    "error": "SSO session expired. Please authenticate again.",
                    "error_code": "SESSION_EXPIRED"
                }
            
            # Get credentials
            credentials = self.sso_handler.get_session_credentials(session_token)
            
            # List bucket contents
            files = self.s3_manager.list_objects(bucket_name, prefix, credentials)
            
            logger.info(f"[TOOL2] Found {len(files)} objects in {bucket_name}")
            
            return {
                "success": True,
                "bucket": bucket_name,
                "prefix": prefix or "/",
                "files": files,
                "count": len(files),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[TOOL2] Error listing bucket contents: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "BUCKET_CONTENTS_ERROR"
            }
    
    # ========================================================================
    # TOOL 3: get_file_metadata
    # ========================================================================
    
    def get_file_metadata(
        self,
        bucket_name: str,
        file_key: str,
        session_token: str
    ) -> Dict[str, Any]:
        """
        Tool 3: Get detailed metadata for a specific S3 file.
        
        Uses S3FileCache DynamoDB table with 24-hour TTL for performance.
        Returns size, type, last modified, storage class, and ETag.
        
        Args:
            bucket_name: Name of the S3 bucket
            file_key: Full path to the file (e.g., "folder/file.txt")
            session_token: Active SSO session token
            
        Returns:
            {
                "success": True,
                "cached": False,
                "bucket": "my-bucket",
                "key": "folder/file.txt",
                "size": 1048576,
                "size_human": "1.0 MB",
                "content_type": "text/plain",
                "last_modified": "2025-12-01T...",
                "storage_class": "STANDARD",
                "etag": "\"abc123...\"",
                "metadata": {...}
            }
        """
        try:
            logger.info(f"[TOOL3] get_file_metadata: bucket={bucket_name}, key={file_key}")
            
            # Validate SSO session
            if not self.sso_handler.is_session_valid(session_token):
                return {
                    "success": False,
                    "error": "SSO session expired",
                    "error_code": "SESSION_EXPIRED"
                }
            
            # STEP 1: Check S3FileCache table first (24-hour TTL)
            cache_key = f"{bucket_name}#{file_key}"
            cached_metadata = self.dynamodb_manager.get_cached_file_metadata(cache_key)
            
            if cached_metadata:
                logger.info(f"[TOOL3] Cache HIT for {cache_key}")
                return {
                    "success": True,
                    "cached": True,
                    "cache_age_hours": cached_metadata.get("cache_age_hours", 0),
                    **cached_metadata
                }
            
            # STEP 2: Cache MISS - fetch from S3
            logger.info(f"[TOOL3] Cache MISS for {cache_key}, fetching from S3")
            credentials = self.sso_handler.get_session_credentials(session_token)
            
            # Get fresh metadata from S3
            metadata = self.s3_manager.get_object_metadata(bucket_name, file_key, credentials)
            
            # STEP 3: Store in S3FileCache table with 24-hour TTL
            self.dynamodb_manager.cache_file_metadata(cache_key, metadata, ttl_hours=24)
            
            logger.info(f"[TOOL3] Metadata cached for {cache_key}")
            
            return {
                "success": True,
                "cached": False,
                **metadata
            }
            
        except Exception as e:
            logger.error(f"[TOOL3] Error getting file metadata: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "METADATA_ERROR"
            }
    
    # ========================================================================
    # TOOL 4: validate_user_access
    # ========================================================================
    
    def validate_user_access(
        self,
        bucket_name: str,
        session_token: str
    ) -> Dict[str, Any]:
        """
        Tool 4: Validate user has read-only access to specified S3 bucket.
        
        Checks IAM permissions via SSO credentials.
        Ensures users have s3:GetObject and s3:ListBucket but NOT s3:PutObject or s3:DeleteObject.
        
        Args:
            bucket_name: Name of the S3 bucket to validate
            session_token: Active SSO session token
            
        Returns:
            {
                "success": True,
                "bucket": "my-bucket",
                "permissions": {
                    "read": True,
                    "write": False,
                    "delete": False,
                    "list": True
                },
                "read_only": True,
                "security_compliant": True
            }
        """
        try:
            logger.info(f"[TOOL4] validate_user_access: bucket={bucket_name}")
            
            # Validate SSO session
            if not self.sso_handler.is_session_valid(session_token):
                return {
                    "success": False,
                    "error": "SSO session expired",
                    "error_code": "SESSION_EXPIRED"
                }
            
            # Get credentials
            credentials = self.sso_handler.get_session_credentials(session_token)
            
            # Check bucket permissions using S3Manager
            permissions = self.s3_manager.check_bucket_permissions(bucket_name, credentials)
            
            # Verify read-only access (security requirement)
            is_read_only = permissions.get("read", False) and not permissions.get("write", False)
            is_compliant = is_read_only and not permissions.get("delete", False)
            
            logger.info(f"[TOOL4] Permissions check: read_only={is_read_only}, compliant={is_compliant}")
            
            return {
                "success": True,
                "bucket": bucket_name,
                "permissions": permissions,
                "read_only": is_read_only,
                "security_compliant": is_compliant,
                "message": "READ-ONLY access confirmed" if is_read_only else "WARNING: Write access detected",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[TOOL4] Error validating access: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "ACCESS_VALIDATION_ERROR"
            }
    
    # ========================================================================
    # TOOL 5: analyze_transfer_request
    # ========================================================================
    
    def analyze_transfer_request(
        self,
        source_bucket: str,
        source_key: str,
        destination_host: str,
        destination_port: int,
        transfer_type: str
    ) -> Dict[str, Any]:
        """
        Tool 5: Analyze transfer request to determine optimal strategy.
        
        Evaluates file size, transfer type, destination, and historical performance.
        Recommends chunking strategy, parallelization, and estimated time.
        
        Args:
            source_bucket: Source S3 bucket name
            source_key: Source file key/path
            destination_host: FTP/SFTP destination host
            destination_port: FTP/SFTP port (21=FTP, 22=SFTP)
            transfer_type: 'ftp' or 'sftp'
            
        Returns:
            {
                "success": True,
                "analysis": {
                    "file_size_bytes": 104857600,
                    "file_size_human": "100 MB",
                    "transfer_type": "sftp",
                    "optimal_strategy": "chunked_parallel",
                    "chunk_size_mb": 10,
                    "parallel_threads": 4,
                    "estimated_duration_sec": 120,
                    "network_latency_ms": 50
                },
                "recommendations": [...]
            }
        """
        try:
            logger.info(f"[TOOL5] analyze_transfer_request: {source_bucket}/{source_key} -> {destination_host}:{destination_port}")
            
            # Use TransferHandler to analyze request
            analysis = self.transfer_handler.analyze_request(
                source_bucket=source_bucket,
                source_key=source_key,
                destination_host=destination_host,
                destination_port=destination_port,
                transfer_type=transfer_type
            )
            
            logger.info(f"[TOOL5] Analysis complete: strategy={analysis.get('optimal_strategy')}")
            
            return {
                "success": True,
                **analysis
            }
            
        except Exception as e:
            logger.error(f"[TOOL5] Error analyzing transfer: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "ANALYSIS_ERROR"
            }
    
    # ========================================================================
    # TOOL 6: predict_transfer_outcome
    # ========================================================================
    
    def predict_transfer_outcome(
        self,
        file_size_bytes: int,
        transfer_type: str,
        destination_region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tool 6: Predict transfer success rate and duration using ML from AgentLearning table.
        
        Queries historical transfer data from DynamoDB AgentLearning table.
        Categorizes file by size and predicts outcome based on past transfers.
        
        Args:
            file_size_bytes: File size in bytes
            transfer_type: 'ftp' or 'sftp'
            destination_region: Optional geographic region
            
        Returns:
            {
                "success": True,
                "prediction": {
                    "success_rate": 0.92,
                    "estimated_duration_seconds": 180,
                    "estimated_duration_human": "3 minutes",
                    "file_size_category": "large",
                    "confidence": "high",
                    "based_on_samples": 47
                },
                "recommendations": [
                    "Large file detected. Consider scheduling during off-peak hours.",
                    "SFTP recommended for better integrity checking."
                ]
            }
        """
        try:
            logger.info(f"[TOOL6] predict_transfer_outcome: size={file_size_bytes}, type={transfer_type}")
            
            # STEP 1: Categorize file size
            if file_size_bytes < 1024 * 1024:  # < 1 MB
                size_category = "small"
            elif file_size_bytes < 100 * 1024 * 1024:  # < 100 MB
                size_category = "medium"
            elif file_size_bytes < 1024 * 1024 * 1024:  # < 1 GB
                size_category = "large"
            else:
                size_category = "very_large"
            
            # STEP 2: Query AgentLearning DynamoDB table for historical data
            # PK: transfer_type, SK: file_size_category
            historical_data = self.dynamodb_manager.get_learning_data(
                transfer_type=transfer_type,
                size_category=size_category
            )
            
            # STEP 3: Calculate predictions
            if historical_data and historical_data.get("sample_count", 0) > 0:
                # Use ML-based predictions from historical data
                success_rate = historical_data.get("success_rate", 0.85)
                avg_duration_sec = historical_data.get("avg_duration_seconds", 60)
                sample_size = historical_data.get("sample_count", 0)
                confidence = "high" if sample_size > 10 else "medium"
            else:
                # Use heuristic estimates (no historical data)
                success_rate = 0.80
                avg_duration_sec = self._estimate_duration(file_size_bytes, transfer_type)
                sample_size = 0
                confidence = "low"
            
            # STEP 4: Generate recommendations
            recommendations = self._get_transfer_recommendations(
                file_size_bytes,
                transfer_type,
                success_rate,
                size_category
            )
            
            logger.info(f"[TOOL6] Prediction: success_rate={success_rate}, duration={avg_duration_sec}s, confidence={confidence}")
            
            return {
                "success": True,
                "prediction": {
                    "success_rate": round(success_rate, 2),
                    "estimated_duration_seconds": int(avg_duration_sec),
                    "estimated_duration_human": self._format_duration(int(avg_duration_sec)),
                    "file_size_category": size_category,
                    "confidence": confidence,
                    "based_on_samples": sample_size
                },
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[TOOL6] Error predicting outcome: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "PREDICTION_ERROR"
            }
    
    # ========================================================================
    # TOOL 7: create_servicenow_tickets (DUAL TICKETS)
    # ========================================================================
    
    def create_servicenow_tickets(
        self,
        requester_email: str,
        source_bucket: str,
        source_file: str,
        destination_server: str,
        environment: str,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Tool 7: Create TWO ServiceNow tickets for audit compliance.
        
        Creates:
        1. User Request Ticket - For requester's tracking
        2. Audit Team Ticket - For compliance and security team
        
        Both tickets linked with same transfer_id for audit trail.
        
        Args:
            requester_email: Email of person requesting transfer
            source_bucket: Source S3 bucket name
            source_file: Source file key/path
            destination_server: Destination FTP/SFTP server details
            environment: 'production', 'staging', or 'development'
            priority: 'critical', 'high', 'medium', or 'low'
            
        Returns:
            {
                "success": True,
                "user_ticket": "INC0010234",
                "audit_ticket": "INC0010235",
                "transfer_id": "TRF-20251203-ABC123",
                "message": "Two ServiceNow tickets created successfully",
                "servicenow_url": "https://dev329630.service-now.com"
            }
        """
        try:
            logger.info(f"[TOOL7] create_servicenow_tickets: requester={requester_email}, env={environment}")
            
            # Generate unique transfer_id for linking both tickets
            transfer_id = f"TRF-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Call ServiceNowHandler to create DUAL tickets
            tickets = self.servicenow_handler.create_dual_tickets(
                requester_email=requester_email,
                source_bucket=source_bucket,
                source_file=source_file,
                destination_server=destination_server,
                environment=environment,
                priority=priority,
                transfer_id=transfer_id
            )
            
            logger.info(f"[TOOL7] ✅ Dual tickets created: user={tickets['user_ticket']}, audit={tickets['audit_ticket']}")
            
            return {
                "success": True,
                "user_ticket": tickets["user_ticket"],
                "audit_ticket": tickets["audit_ticket"],
                "transfer_id": transfer_id,
                "message": "Two ServiceNow tickets created successfully for audit compliance",
                "servicenow_url": self.config.get("servicenow", {}).get("instance_url"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[TOOL7] Error creating ServiceNow tickets: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "SERVICENOW_ERROR"
            }
    
    # ========================================================================
    # TOOL 8: execute_transfer (AWS Step Functions Workflow)
    # ========================================================================
    
    def execute_transfer(
        self,
        transfer_id: str,
        source_bucket: str,
        source_key: str,
        destination_config: Dict[str, Any],
        servicenow_tickets: Dict[str, str],
        session_token: str
    ) -> Dict[str, Any]:
        """
        Tool 8: Execute file transfer using AWS Step Functions state machine.
        
        Workflow steps:
        1. Validate Request
        2. Update ServiceNow Tickets (in progress)
        3. Download from S3 (streaming)
        4. Transfer to FTP/SFTP (chunked, parallel)
        5. Update ServiceNow Tickets (completed)
        6. Send Notification
        
        Args:
            transfer_id: Unique transfer identifier
            source_bucket: Source S3 bucket
            source_key: Source file key/path
            destination_config: {
                "type": "ftp" | "sftp",
                "host": "ftp.example.com",
                "port": 21,
                "username": "ftpuser",
                "password": "***",
                "path": "/uploads/"
            }
            servicenow_tickets: {
                "user_ticket": "INC0010234",
                "audit_ticket": "INC0010235"
            }
            session_token: Active SSO session token
            
        Returns:
            {
                "success": True,
                "transfer_id": "TRF-20251203-ABC123",
                "execution_arn": "arn:aws:states:us-east-1:...",
                "status": "in_progress",
                "step_functions_console": "https://console.aws.amazon.com/states/...",
                "estimated_completion": "2025-12-03T15:30:00Z"
            }
        """
        try:
            logger.info(f"[TOOL8] execute_transfer: transfer_id={transfer_id}, bucket={source_bucket}, key={source_key}")
            
            # STEP 1: Validate SSO session (critical security check)
            if not self.sso_handler.is_session_valid(session_token):
                logger.error(f"[TOOL8] Cannot start transfer: SSO session expired")
                return {
                    "success": False,
                    "error": "SSO session expired. Cannot start transfer without valid authentication.",
                    "error_code": "SESSION_EXPIRED"
                }
            
            # STEP 2: Get temporary AWS credentials
            credentials = self.sso_handler.get_session_credentials(session_token)
            
            # STEP 3: Store transfer request in TransferRequests DynamoDB table
            transfer_record = {
                "transfer_id": transfer_id,
                "source_bucket": source_bucket,
                "source_key": source_key,
                "destination": destination_config,
                "servicenow_tickets": servicenow_tickets,
                "status": "initiating",
                "created_at": datetime.now().isoformat(),
                "ttl": int((datetime.now() + timedelta(days=90)).timestamp())  # 90-day retention
            }
            
            self.dynamodb_manager.store_transfer_request(transfer_record)
            logger.info(f"[TOOL8] Transfer record stored in DynamoDB")
            
            # STEP 4: Start AWS Step Functions workflow
            execution_arn = self.transfer_handler.start_transfer_workflow(
                transfer_id=transfer_id,
                source_bucket=source_bucket,
                source_key=source_key,
                destination_config=destination_config,
                servicenow_tickets=servicenow_tickets,
                credentials=credentials
            )
            
            logger.info(f"[TOOL8] ✅ Step Functions workflow started: {execution_arn}")
            
            # STEP 5: Update transfer status
            self.dynamodb_manager.update_transfer_status(transfer_id, "in_progress")
            
            return {
                "success": True,
                "transfer_id": transfer_id,
                "execution_arn": execution_arn,
                "status": "in_progress",
                "step_functions_console": f"https://console.aws.amazon.com/states/home?region=us-east-1#/executions/details/{execution_arn}",
                "message": "Transfer workflow started successfully. Monitor progress in Step Functions console.",
                "servicenow_tickets": servicenow_tickets,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[TOOL8] Error executing transfer: {str(e)}", exc_info=True)
            
            # Update status to failed
            try:
                self.dynamodb_manager.update_transfer_status(transfer_id, "failed", error=str(e))
            except:
                pass
            
            return {
                "success": False,
                "error": str(e),
                "error_code": "TRANSFER_EXECUTION_ERROR",
                "transfer_id": transfer_id
            }
    
    # ========================================================================
    # TOOL 9: get_transfer_history
    # ========================================================================
    
    def get_transfer_history(
        self,
        user_id: str,
        limit: int = 10,
        status_filter: str = "all"
    ) -> Dict[str, Any]:
        """
        Tool 9: Retrieve user's transfer history from TransferRequests table.
        
        Uses GSI on user_id for efficient querying.
        Returns last N transfers with status, duration, and ServiceNow tickets.
        
        Args:
            user_id: User identifier
            limit: Maximum number of records to return (default: 10, max: 50)
            status_filter: 'all', 'completed', 'in_progress', 'failed'
            
        Returns:
            {
                "success": True,
                "user_id": "user@example.com",
                "transfers": [
                    {
                        "transfer_id": "TRF-20251203-ABC123",
                        "source": "my-bucket/file.txt",
                        "destination": "ftp.example.com",
                        "status": "completed",
                        "duration_seconds": 180,
                        "servicenow_tickets": {...},
                        "created_at": "2025-12-03T14:00:00Z",
                        "completed_at": "2025-12-03T14:03:00Z"
                    }
                ],
                "count": 5,
                "filter": "all"
            }
        """
        try:
            logger.info(f"[TOOL9] get_transfer_history: user_id={user_id}, limit={limit}, filter={status_filter}")
            
            # Query TransferRequests table using GSI on user_id
            history = self.dynamodb_manager.query_user_transfers(
                user_id=user_id,
                limit=min(limit, 50),  # Cap at 50
                status_filter=status_filter
            )
            
            logger.info(f"[TOOL9] Found {len(history)} transfers for user {user_id}")
            
            return {
                "success": True,
                "user_id": user_id,
                "transfers": history,
                "count": len(history),
                "filter": status_filter,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[TOOL9] Error getting transfer history: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_code": "HISTORY_ERROR"
            }
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _estimate_duration(self, file_size_bytes: int, transfer_type: str) -> int:
        """
        Estimate transfer duration based on file size and type.
        
        Assumptions:
        - FTP: 10 MB/s average
        - SFTP: 5 MB/s average (slower due to encryption overhead)
        - Add 30 second overhead for connection, validation, etc.
        """
        speed_mbps = 10 if transfer_type == "ftp" else 5
        file_size_mb = file_size_bytes / (1024 * 1024)
        duration_sec = file_size_mb / speed_mbps
        return int(duration_sec) + 30  # Add overhead
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} {secs} second{'s' if secs != 1 else ''}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
    
    def _get_transfer_recommendations(
        self,
        file_size_bytes: int,
        transfer_type: str,
        success_rate: float,
        size_category: str
    ) -> List[str]:
        """Generate intelligent transfer recommendations."""
        recommendations = []
        
        # Large file recommendations
        if file_size_bytes > 1024 * 1024 * 1024:  # > 1 GB
            recommendations.append("⚠️  Large file detected (>1 GB). Consider scheduling transfer during off-peak hours.")
            recommendations.append("✅ SFTP recommended for better integrity checking on large files.")
            recommendations.append("💡 Chunked parallel upload will be used automatically for faster transfer.")
        
        # Success rate recommendations
        if success_rate < 0.7:
            recommendations.append("⚠️  Low historical success rate (<70%). Review destination server availability.")
            recommendations.append("✅ Retry mechanism with exponential backoff will be enabled automatically.")
            recommendations.append("💡 Consider contacting destination server administrator to verify connectivity.")
        elif success_rate >= 0.9:
            recommendations.append("✅ High success rate (>90%) for similar transfers. Expected smooth operation.")
        
        # Protocol recommendations
        if transfer_type == "ftp":
            recommendations.append("⚠️  FTP detected. Consider using SFTP for encrypted transfer (more secure).")
        else:
            recommendations.append("✅ SFTP selected. Transfer will be encrypted end-to-end.")
        
        # Default message if no concerns
        if not recommendations:
            recommendations.append("✅ Transfer looks optimal! No special considerations needed.")
            recommendations.append("💡 Estimated duration and success rate are based on historical data.")
        
        return recommendations
