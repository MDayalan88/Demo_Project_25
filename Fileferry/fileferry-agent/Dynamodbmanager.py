"""
DynamoDB Manager - State and data management
Follows Azure Cosmos DB best practices adapted for DynamoDB
"""

import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from aws_xray_sdk.core import xray_recorder

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DynamoDBManager:
    """
    Centralized DynamoDB operations with best practices:
    - Efficient partition key usage
    - Batch operations where possible
    - TTL for automatic cleanup
    - Conditional writes for consistency
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize DynamoDB Manager
        
        Args:
            config: Configuration with DynamoDB settings
        """
        self.config = config
        region = config.get('aws', {}).get('region', 'us-east-1')
        
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # Table references
        self.transfers_table = self.dynamodb.Table('FileFerry-TransferRequests')
        self.learning_table = self.dynamodb.Table('FileFerry-AgentLearning')
        self.context_table = self.dynamodb.Table('FileFerry-UserContext')
        self.sessions_table = self.dynamodb.Table('FileFerry-ActiveSessions')
        self.cache_table = self.dynamodb.Table('FileFerry-S3FileCache')
        
        logger.info("✅ DynamoDB Manager initialized")
    
    @xray_recorder.capture('store_transfer_request')
    async def store_transfer_request(self, user_id: str, transfer_data: Dict) -> str:
        """
        Store transfer request in DynamoDB
        Partition Key: userId, Sort Key: requestId
        
        Args:
            user_id: User ID
            transfer_data: Transfer details
            
        Returns:
            Request ID
        """
        request_id = f"req_{int(datetime.utcnow().timestamp() * 1000)}"
        
        item = {
            'userId': user_id,  # Partition Key
            'requestId': request_id,  # Sort Key
            'timestamp': datetime.utcnow().isoformat(),
            'fileName': transfer_data.get('file_name'),
            'bucketName': transfer_data.get('bucket_name'),
            'region': transfer_data.get('region'),
            'destinationType': transfer_data.get('destination_type'),
            'status': 'initiated',
            'servicenowTickets': transfer_data.get('tickets', []),
            'estimatedDuration': transfer_data.get('estimated_duration'),
            'predictedSuccessRate': transfer_data.get('success_rate'),
            'transferPlan': transfer_data.get('transfer_plan', {})
        }
        
        try:
            self.transfers_table.put_item(Item=item)
            logger.info(f"Stored transfer request: {request_id} for user {user_id}")
            return request_id
        except Exception as e:
            logger.error(f"Error storing transfer request: {str(e)}", exc_info=True)
            raise
    
    @xray_recorder.capture('query_user_transfers')
    async def query_user_transfers(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Query all transfers for a user
        Efficient: Single partition query
        
        Args:
            user_id: User ID
            limit: Maximum records
            
        Returns:
            List of transfers
        """
        try:
            response = self.transfers_table.query(
                KeyConditionExpression=Key('userId').eq(user_id),
                ScanIndexForward=False,  # DESC order
                Limit=limit
            )
            
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error querying transfers: {str(e)}", exc_info=True)
            return []
    
    @xray_recorder.capture('store_learning_data')
    async def store_learning_data(self, learning_data: Dict):
        """
        Store transfer outcome for agent learning
        Partition Key: transferType, Sort Key: timestamp
        TTL: 1 year (automatic cleanup)
        
        Args:
            learning_data: Learning data dictionary
        """
        file_size = learning_data.get('file_size_bytes', 0)
        
        item = {
            'transferType': learning_data['transfer_type'],  # PK
            'timestamp': datetime.utcnow().isoformat(),  # SK
            'outcome': learning_data['outcome'],
            'fileSizeBytes': file_size,
            'fileSizeCategory': self._categorize_size(file_size),
            'durationSeconds': learning_data.get('duration_seconds'),
            'transferSpeedMbps': learning_data.get('speed_mbps'),
            'chunkSize': learning_data.get('chunk_size_mb'),
            'parallelUploads': learning_data.get('parallel_uploads'),
            'errorCount': learning_data.get('error_count', 0),
            'sourceRegion': learning_data.get('source_region'),
            'expirationTime': int((datetime.utcnow() + timedelta(days=365)).timestamp())  # TTL
        }
        
        try:
            self.learning_table.put_item(Item=item)
            logger.info(f"Stored learning data for {learning_data['transfer_type']}")
        except Exception as e:
            logger.error(f"Error storing learning data: {str(e)}", exc_info=True)
    
    @xray_recorder.capture('query_learning_data')
    async def query_learning_data(self, transfer_type: str, limit: int = 100) -> List[Dict]:
        """
        Query historical learning data
        Partition Key query: Very efficient
        
        Args:
            transfer_type: Transfer type (sftp/ftp)
            limit: Maximum records
            
        Returns:
            List of historical transfers
        """
        try:
            response = self.learning_table.query(
                KeyConditionExpression=Key('transferType').eq(transfer_type),
                ScanIndexForward=False,
                Limit=limit
            )
            
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error querying learning data: {str(e)}", exc_info=True)
            return []
    
    @xray_recorder.capture('load_user_context')
    async def load_user_context(self, user_id: str) -> Dict:
        """
        Load user context from DynamoDB
        
        Args:
            user_id: User ID
            
        Returns:
            User context dictionary
        """
        try:
            response = self.context_table.get_item(Key={'userId': user_id})
            
            if 'Item' in response:
                return response['Item']
            else:
                # Create default context
                default_context = {
                    'userId': user_id,
                    'history': [],
                    'frequent_buckets': [],
                    'created_at': datetime.utcnow().isoformat()
                }
                return default_context
                
        except Exception as e:
            logger.error(f"Error loading user context: {str(e)}", exc_info=True)
            return {'userId': user_id, 'history': [], 'frequent_buckets': []}
    
    @xray_recorder.capture('store_interaction')
    async def store_interaction(
        self, 
        user_id: str, 
        request: str, 
        response: str,
        conversation_id: str
    ):
        """
        Store user-agent interaction
        
        Args:
            user_id: User ID
            request: User request
            response: Agent response
            conversation_id: Conversation ID
        """
        request_id = f"int_{int(datetime.utcnow().timestamp() * 1000)}"
        
        item = {
            'userId': user_id,
            'requestId': request_id,
            'conversationId': conversation_id,
            'request': request,
            'response': response,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            self.transfers_table.put_item(Item=item)
        except Exception as e:
            logger.error(f"Error storing interaction: {str(e)}", exc_info=True)
    
    @xray_recorder.capture('cache_s3_metadata')
    async def cache_s3_metadata(self, bucket: str, key: str, metadata: Dict):
        """
        Cache S3 file metadata
        Partition Key: bucketName, Sort Key: fileKey
        TTL: 24 hours
        
        Args:
            bucket: Bucket name
            key: File key
            metadata: Metadata dictionary
        """
        item = {
            'bucketName': bucket,  # PK
            'fileKey': key,  # SK
            'metadata': metadata,
            'cached_at': datetime.utcnow().isoformat(),
            'expirationTime': int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        }
        
        try:
            self.cache_table.put_item(Item=item)
        except Exception as e:
            logger.error(f"Error caching metadata: {str(e)}", exc_info=True)
    
    @xray_recorder.capture('get_cached_metadata')
    async def get_cached_metadata(self, bucket: str, key: str) -> Optional[Dict]:
        """
        Get cached metadata (TTL handled by DynamoDB)
        
        Args:
            bucket: Bucket name
            key: File key
            
        Returns:
            Cached metadata or None
        """
        try:
            response = self.cache_table.get_item(
                Key={'bucketName': bucket, 'fileKey': key}
            )
            
            if 'Item' in response:
                return response['Item']['metadata']
        except Exception as e:
            logger.error(f"Error getting cached metadata: {str(e)}", exc_info=True)
        
        return None
    
    def _categorize_size(self, size_bytes: int) -> str:
        """Categorize file size for efficient querying"""
        if size_bytes < 10 * 1024 * 1024:
            return "small"
        elif size_bytes < 100 * 1024 * 1024:
            return "medium"
        elif size_bytes < 1024 * 1024 * 1024:
            return "large"
        else:
            return "xlarge"