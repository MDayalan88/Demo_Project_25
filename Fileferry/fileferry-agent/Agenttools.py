"""
Agent Tools - Function implementations for Bedrock AI Agent
Executes specific operations requested by Claude Sonnet 4.5
"""

import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime
from botocore.exceptions import ClientError
from aws_xray_sdk.core import xray_recorder

from ..handlers.sso_handler import SSOHandler
from ..storage.dynamodb_manager import DynamoDBManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AgentTools:
    """
    Tool implementations for FileFerry AI Agent
    Each tool is a function that Claude can call to perform actions
    """
    
    def __init__(self, config: Dict[str, Any], db_manager: DynamoDBManager, sso_handler: SSOHandler):
        """
        Initialize Agent Tools
        
        Args:
            config: Configuration dictionary
            db_manager: DynamoDB manager instance
            sso_handler: SSO handler instance
        """
        self.config = config
        self.db_manager = db_manager
        self.sso_handler = sso_handler
        
        # Cache for S3 client per region
        self._s3_clients: Dict[str, Any] = {}
        
        logger.info("✅ Agent Tools initialized")
    
    async def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name
        
        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool
            
        Returns:
            Tool execution result
        """
        tool_map = {
            'list_s3_buckets': self.list_s3_buckets,
            'list_bucket_contents': self.list_bucket_contents,
            'get_file_metadata': self.get_file_metadata,
            'validate_user_access': self.validate_user_access,
            'analyze_transfer_request': self.analyze_transfer_request,
            'predict_transfer_outcome': self.predict_transfer_outcome,
            'create_servicenow_tickets': self.create_servicenow_tickets,
            'execute_transfer': self.execute_transfer,
            'get_transfer_history': self.get_transfer_history
        }
        
        if tool_name not in tool_map:
            logger.error(f"Unknown tool: {tool_name}")
            return {
                'status': 'error',
                'error': f'Unknown tool: {tool_name}'
            }
        
        try:
            logger.info(f"Executing tool: {tool_name}")
            result = await tool_map[tool_name](**tool_input)
            logger.info(f"Tool {tool_name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'tool': tool_name
            }
    
    @xray_recorder.capture('list_s3_buckets')
    async def list_s3_buckets(self, region: Optional[str] = None) -> Dict[str, Any]:
        """
        List all S3 buckets accessible to the user
        
        Args:
            region: Optional region filter
            
        Returns:
            List of buckets with metadata
        """
        try:
            # Authenticate with SSO
            session_data = await self.sso_handler.authenticate(region)
            boto_session = self.sso_handler.get_boto3_session(session_data)
            s3_client = boto_session.client('s3')
            
            # List buckets
            response = s3_client.list_buckets()
            buckets = response.get('Buckets', [])
            
            # Filter by region if specified
            if region:
                filtered_buckets = []
                for bucket in buckets:
                    try:
                        location = s3_client.get_bucket_location(Bucket=bucket['Name'])
                        bucket_region = location['LocationConstraint'] or 'us-east-1'
                        if bucket_region == region:
                            bucket['Region'] = bucket_region
                            filtered_buckets.append(bucket)
                    except Exception as e:
                        logger.warning(f"Could not get location for bucket {bucket['Name']}: {str(e)}")
                buckets = filtered_buckets
            
            # Format response
            bucket_list = []
            for bucket in buckets:
                bucket_list.append({
                    'name': bucket['Name'],
                    'creation_date': bucket['CreationDate'].isoformat(),
                    'region': bucket.get('Region', 'us-east-1')
                })
            
            # Logout after operation
            await self.sso_handler.logout(session_data)
            
            return {
                'status': 'success',
                'buckets': bucket_list,
                'count': len(bucket_list)
            }
            
        except ClientError as e:
            logger.error(f"S3 ClientError in list_buckets: {str(e)}")
            return {
                'status': 'error',
                'error': f"S3 Error: {e.response['Error']['Message']}"
            }
        except Exception as e:
            logger.error(f"Error listing S3 buckets: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @xray_recorder.capture('list_bucket_contents')
    async def list_bucket_contents(
        self, 
        bucket_name: str, 
        prefix: Optional[str] = None,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List contents of an S3 bucket
        
        Args:
            bucket_name: Name of the bucket
            prefix: Optional prefix to filter objects
            region: AWS region
            
        Returns:
            List of objects in the bucket
        """
        try:
            # Authenticate
            session_data = await self.sso_handler.authenticate(region)
            boto_session = self.sso_handler.get_boto3_session(session_data)
            s3_client = boto_session.client('s3', region_name=region)
            
            # List objects
            params = {'Bucket': bucket_name}
            if prefix:
                params['Prefix'] = prefix
            
            response = s3_client.list_objects_v2(**params)
            objects = response.get('Contents', [])
            
            # Format response
            object_list = []
            for obj in objects:
                object_list.append({
                    'key': obj['Key'],
                    'size_bytes': obj['Size'],
                    'size_mb': round(obj['Size'] / (1024 * 1024), 2),
                    'last_modified': obj['LastModified'].isoformat(),
                    'storage_class': obj.get('StorageClass', 'STANDARD')
                })
            
            # Logout
            await self.sso_handler.logout(session_data)
            
            return {
                'status': 'success',
                'bucket': bucket_name,
                'prefix': prefix,
                'objects': object_list,
                'count': len(object_list)
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                return {
                    'status': 'error',
                    'error': f"Bucket '{bucket_name}' does not exist"
                }
            elif error_code == 'AccessDenied':
                return {
                    'status': 'error',
                    'error': f"Access denied to bucket '{bucket_name}'"
                }
            else:
                return {
                    'status': 'error',
                    'error': f"S3 Error: {e.response['Error']['Message']}"
                }
        except Exception as e:
            logger.error(f"Error listing bucket contents: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @xray_recorder.capture('get_file_metadata')
    async def get_file_metadata(
        self, 
        bucket_name: str, 
        file_key: str,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed metadata for an S3 object
        
        Args:
            bucket_name: Bucket name
            file_key: Object key
            region: AWS region
            
        Returns:
            File metadata
        """
        try:
            # Check cache first
            cached = await self.db_manager.get_cached_metadata(bucket_name, file_key)
            if cached:
                logger.info(f"Cache hit for {bucket_name}/{file_key}")
                return {
                    'status': 'success',
                    'metadata': cached,
                    'cached': True
                }
            
            # Authenticate
            session_data = await self.sso_handler.authenticate(region)
            boto_session = self.sso_handler.get_boto3_session(session_data)
            s3_client = boto_session.client('s3', region_name=region)
            
            # Get object metadata
            response = s3_client.head_object(Bucket=bucket_name, Key=file_key)
            
            metadata = {
                'bucket': bucket_name,
                'key': file_key,
                'size_bytes': response['ContentLength'],
                'size_mb': round(response['ContentLength'] / (1024 * 1024), 2),
                'last_modified': response['LastModified'].isoformat(),
                'content_type': response.get('ContentType', 'unknown'),
                'storage_class': response.get('StorageClass', 'STANDARD'),
                'encryption': response.get('ServerSideEncryption', 'none'),
                'etag': response.get('ETag', '').strip('"'),
                'version_id': response.get('VersionId')
            }
            
            # Cache metadata
            await self.db_manager.cache_s3_metadata(bucket_name, file_key, metadata)
            
            # Logout
            await self.sso_handler.logout(session_data)
            
            return {
                'status': 'success',
                'metadata': metadata,
                'cached': False
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return {
                    'status': 'error',
                    'error': f"File '{file_key}' not found in bucket '{bucket_name}'"
                }
            elif error_code == 'AccessDenied':
                return {
                    'status': 'error',
                    'error': f"Access denied to '{file_key}' in bucket '{bucket_name}'"
                }
            else:
                return {
                    'status': 'error',
                    'error': f"S3 Error: {e.response['Error']['Message']}"
                }
        except Exception as e:
            logger.error(f"Error getting file metadata: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def validate_user_access(
        self, 
        bucket_name: str, 
        file_key: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Validate user has read access to S3 object
        
        Args:
            bucket_name: Bucket name
            file_key: Object key
            user_id: User ID
            
        Returns:
            Validation result
        """
        try:
            # Try to get file metadata (validates access)
            result = await self.get_file_metadata(bucket_name, file_key)
            
            if result['status'] == 'success':
                logger.info(f"User {user_id} has access to {bucket_name}/{file_key}")
                return {
                    'status': 'success',
                    'access_granted': True,
                    'message': f"User has read access to {file_key}"
                }
            else:
                logger.warning(f"User {user_id} denied access to {bucket_name}/{file_key}")
                return {
                    'status': 'success',
                    'access_granted': False,
                    'message': result.get('error', 'Access denied')
                }
                
        except Exception as e:
            logger.error(f"Error validating access: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def analyze_transfer_request(
        self,
        file_metadata: Dict[str, Any],
        destination_type: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Analyze transfer request and recommend strategy
        
        Args:
            file_metadata: File metadata from get_file_metadata
            destination_type: 'sftp' or 'ftp'
            user_id: User ID
            
        Returns:
            Transfer analysis with recommended strategy
        """
        try:
            metadata = file_metadata.get('metadata', file_metadata)
            file_size = metadata.get('size_bytes', 0)
            
            # Categorize file size
            if file_size < 10 * 1024 * 1024:  # < 10MB
                category = "small"
                strategy = {
                    "chunk_size_mb": 0,  # No chunking
                    "parallel_uploads": 1,
                    "compression": False,
                    "estimated_duration_seconds": max(5, file_size // (5 * 1024 * 1024)),
                    "risk_level": "low"
                }
            elif file_size < 100 * 1024 * 1024:  # < 100MB
                category = "medium"
                strategy = {
                    "chunk_size_mb": 10,
                    "parallel_uploads": 4,
                    "compression": True,
                    "estimated_duration_seconds": file_size // (10 * 1024 * 1024),
                    "risk_level": "low"
                }
            elif file_size < 1024 * 1024 * 1024:  # < 1GB
                category = "large"
                strategy = {
                    "chunk_size_mb": 20,
                    "parallel_uploads": 8,
                    "compression": True,
                    "estimated_duration_seconds": file_size // (15 * 1024 * 1024),
                    "risk_level": "medium"
                }
            else:  # > 1GB
                category = "xlarge"
                strategy = {
                    "chunk_size_mb": 50,
                    "parallel_uploads": 16,
                    "compression": True,
                    "estimated_duration_seconds": file_size // (20 * 1024 * 1024),
                    "risk_level": "high"
                }
            
            return {
                'status': 'success',
                'file_info': {
                    'name': metadata.get('key', '').split('/')[-1],
                    'size_bytes': file_size,
                    'size_mb': metadata.get('size_mb', 0),
                    'bucket': metadata.get('bucket'),
                    'region': metadata.get('region', 'us-east-1'),
                    'category': category
                },
                'recommended_strategy': strategy,
                'destination_type': destination_type
            }
            
        except Exception as e:
            logger.error(f"Error analyzing transfer: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def predict_transfer_outcome(
        self,
        file_size_bytes: int,
        transfer_type: str,
        source_region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Predict transfer outcome using historical data
        
        Args:
            file_size_bytes: File size in bytes
            transfer_type: 'sftp' or 'ftp'
            source_region: AWS region
            
        Returns:
            Prediction with success rate and estimated duration
        """
        try:
            # Query historical learning data from DynamoDB
            learning_data = await self.db_manager.query_learning_data(
                transfer_type=transfer_type,
                limit=100
            )
            
            if not learning_data or len(learning_data) < 20:
                # Not enough data for confident prediction
                return {
                    'status': 'success',
                    'predicted_success_rate': 0.85,  # Conservative estimate
                    'predicted_duration_seconds': max(30, file_size_bytes // (10 * 1024 * 1024)),
                    'sample_size': len(learning_data),
                    'confidence': 'low',
                    'message': 'Limited historical data available'
                }
            
            # Filter by similar file size (±50%)
            size_min = file_size_bytes * 0.5
            size_max = file_size_bytes * 1.5
            similar_transfers = [
                item for item in learning_data 
                if size_min <= item.get('fileSizeBytes', 0) <= size_max
            ]
            
            if not similar_transfers:
                similar_transfers = learning_data  # Use all data
            
            # Calculate success rate
            success_count = sum(1 for item in similar_transfers if item.get('outcome') == 'success')
            success_rate = success_count / len(similar_transfers)
            
            # Calculate average duration
            durations = [item.get('durationSeconds', 0) for item in similar_transfers if item.get('outcome') == 'success']
            avg_duration = sum(durations) / len(durations) if durations else file_size_bytes // (10 * 1024 * 1024)
            
            # Determine confidence
            if len(similar_transfers) >= 50:
                confidence = 'high'
            elif len(similar_transfers) >= 20:
                confidence = 'medium'
            else:
                confidence = 'low'
            
            return {
                'status': 'success',
                'predicted_success_rate': round(success_rate, 3),
                'predicted_duration_seconds': int(avg_duration),
                'sample_size': len(similar_transfers),
                'confidence': confidence,
                'message': f'Prediction based on {len(similar_transfers)} similar transfers'
            }
            
        except Exception as e:
            logger.error(f"Error predicting outcome: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def create_servicenow_tickets(
        self,
        user_id: str,
        transfer_details: Dict[str, Any],
        assignment_group: str = "DataOps"
    ) -> Dict[str, Any]:
        """
        Create dual ServiceNow tickets (user + audit)
        
        Args:
            user_id: User ID
            transfer_details: Transfer details
            assignment_group: ServiceNow assignment group
            
        Returns:
            Ticket IDs
        """
        try:
            from ..handlers.servicenow_handler import ServiceNowHandler
            
            snow_handler = ServiceNowHandler(self.config)
            result = await snow_handler.create_dual_tickets(
                user_id=user_id,
                transfer_details=transfer_details,
                assignment_group=assignment_group
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating ServiceNow tickets: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def execute_transfer(
        self,
        user_id: str,
        transfer_plan: Dict[str, Any],
        servicenow_tickets: List[str]
    ) -> Dict[str, Any]:
        """
        Execute file transfer (initiates Step Functions)
        
        Args:
            user_id: User ID
            transfer_plan: Transfer plan from analyze_transfer_request
            servicenow_tickets: ServiceNow ticket IDs
            
        Returns:
            Transfer execution result
        """
        try:
            from ..handlers.transfer_handler import TransferHandler
            
            transfer_handler = TransferHandler(self.config, self.sso_handler)
            result = await transfer_handler.initiate_transfer(
                user_id=user_id,
                transfer_plan=transfer_plan,
                servicenow_tickets=servicenow_tickets
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing transfer: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def get_transfer_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get user's transfer history
        
        Args:
            user_id: User ID
            limit: Maximum records to return
            
        Returns:
            Transfer history
        """
        try:
            history = await self.db_manager.query_user_transfers(user_id, limit)
            
            return {
                'status': 'success',
                'user_id': user_id,
                'transfers': history,
                'count': len(history)
            }
            
        except Exception as e:
            logger.error(f"Error getting transfer history: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }