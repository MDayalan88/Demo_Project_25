"""
DynamoDB Manager - Centralized DynamoDB operations with best practices
Handles all database interactions for transfer requests, learning data, user context
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
from aws_xray_sdk.core import xray_recorder
from botocore.exceptions import ClientError

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class DynamoDBManager:
    """
    Manages all DynamoDB operations with optimized partition key usage
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize DynamoDB manager with configuration

        Args:
            config: Configuration dictionary with table names
        """
        self.config = config
        self.region = config.get('aws', {}).get('region', 'us-east-1')
        
        # Initialize DynamoDB resource
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        
        # Table references
        table_config = config.get('dynamodb', {}).get('tables', {})
        self.transfer_requests_table = self.dynamodb.Table(
            table_config.get('transfer_requests', 'FileFerry-TransferRequests')
        )
        self.agent_learning_table = self.dynamodb.Table(
            table_config.get('agent_learning', 'FileFerry-AgentLearning')
        )
        self.user_context_table = self.dynamodb.Table(
            table_config.get('user_context', 'FileFerry-UserContext')
        )
        self.active_sessions_table = self.dynamodb.Table(
            table_config.get('active_sessions', 'FileFerry-ActiveSessions')
        )
        self.s3_file_cache_table = self.dynamodb.Table(
            table_config.get('s3_file_cache', 'FileFerry-S3FileCache')
        )
        
        logger.info("Initialized DynamoDBManager")

    # Transfer Requests Operations

    @xray_recorder.capture('store_transfer_request')
    async def store_transfer_request(
        self,
        user_id: str,
        transfer_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store transfer request in DynamoDB
        Partition key: userId, Sort key: requestId

        Args:
            user_id: User identifier
            transfer_request: Transfer request data

        Returns:
            Dict containing stored item
        """
        try:
            request_id = transfer_request.get('request_id') or self._generate_id()
            timestamp = datetime.utcnow().isoformat()
            
            item = {
                'userId': user_id,
                'requestId': request_id,
                'timestamp': timestamp,
                'status': transfer_request.get('status', 'pending'),
                'sourceBucket': transfer_request.get('bucket_name'),
                'sourceKey': transfer_request.get('file_key'),
                'destinationType': transfer_request.get('destination_type'),
                'destinationHost': transfer_request.get('destination_host'),
                'fileSize': transfer_request.get('file_size', 0),
                'executionArn': transfer_request.get('execution_arn'),
                'servicenowTickets': json.dumps(transfer_request.get('servicenow_tickets', {})),
                'transferStrategy': json.dumps(transfer_request.get('recommendations', {})),
                'metadata': json.dumps(transfer_request.get('metadata', {}))
            }
            
            self.transfer_requests_table.put_item(Item=item)
            
            logger.info(f"Stored transfer request {request_id} for user {user_id}")
            
            return {
                'success': True,
                'request_id': request_id,
                'item': item
            }
            
        except ClientError as e:
            logger.error(f"Error storing transfer request: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    @xray_recorder.capture('query_user_transfers')
    async def query_user_transfers(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query transfer requests for a specific user
        Efficient single-partition query

        Args:
            user_id: User identifier
            limit: Maximum number of items to return

        Returns:
            List of transfer requests
        """
        try:
            response = self.transfer_requests_table.query(
                KeyConditionExpression=Key('userId').eq(user_id),
                ScanIndexForward=False,  # DESC order by timestamp
                Limit=limit
            )
            
            items = response.get('Items', [])
            
            # Parse JSON fields
            for item in items:
                if 'servicenowTickets' in item:
                    item['servicenow_tickets'] = json.loads(item['servicenowTickets'])
                if 'transferStrategy' in item:
                    item['transfer_strategy'] = json.loads(item['transferStrategy'])
                if 'metadata' in item:
                    item['metadata'] = json.loads(item['metadata'])
            
            logger.info(f"Retrieved {len(items)} transfers for user {user_id}")
            
            return items
            
        except ClientError as e:
            logger.error(f"Error querying user transfers: {str(e)}", exc_info=True)
            return []

    @xray_recorder.capture('update_transfer_status')
    async def update_transfer_status(
        self,
        user_id: str,
        request_id: str,
        status: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update transfer request status

        Args:
            user_id: User identifier
            request_id: Request identifier
            status: New status
            additional_data: Optional additional data to update

        Returns:
            Dict containing update result
        """
        try:
            update_expr = "SET #status = :status, updatedAt = :updated"
            expr_attr_names = {'#status': 'status'}
            expr_attr_values = {
                ':status': status,
                ':updated': datetime.utcnow().isoformat()
            }
            
            # Add additional data to update expression
            if additional_data:
                for key, value in additional_data.items():
                    update_expr += f", {key} = :{key}"
                    expr_attr_values[f':{key}'] = value
            
            response = self.transfer_requests_table.update_item(
                Key={'userId': user_id, 'requestId': request_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues='ALL_NEW'
            )
            
            logger.info(f"Updated transfer {request_id} status to {status}")
            
            return {
                'success': True,
                'item': response.get('Attributes')
            }
            
        except ClientError as e:
            logger.error(f"Error updating transfer status: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    # Agent Learning Operations

    @xray_recorder.capture('store_learning_data')
    async def store_learning_data(
        self,
        transfer_type: str,
        transfer_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store transfer outcome for agent learning
        Partition key: transferType, Sort key: timestamp
        TTL: 1 year

        Args:
            transfer_type: Type of transfer (S3_TO_FTP, S3_TO_SFTP)
            transfer_result: Transfer execution result

        Returns:
            Dict containing stored item
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            ttl = int((datetime.utcnow() + timedelta(days=365)).timestamp())
            
            # Categorize file size
            file_size = transfer_result.get('file_size', 0)
            if file_size < 100 * 1024 * 1024:
                size_category = 'small'
            elif file_size < 1024 * 1024 * 1024:
                size_category = 'medium'
            else:
                size_category = 'large'
            
            item = {
                'transferType': transfer_type,
                'timestamp': timestamp,
                'fileSizeCategory': size_category,
                'fileSize': file_size,
                'status': transfer_result.get('status'),
                'durationSeconds': transfer_result.get('duration_seconds', 0),
                'chunkSize': transfer_result.get('chunk_size', 0),
                'parallelThreads': transfer_result.get('parallel_threads', 1),
                'compressionEnabled': transfer_result.get('compression_enabled', False),
                'errorDetails': json.dumps(transfer_result.get('error_details', {})),
                'ttl': ttl
            }
            
            self.agent_learning_table.put_item(Item=item)
            
            logger.info(f"Stored learning data for {transfer_type} ({size_category})")
            
            return {
                'success': True,
                'item': item
            }
            
        except ClientError as e:
            logger.error(f"Error storing learning data: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    @xray_recorder.capture('query_learning_data')
    async def query_learning_data(
        self,
        transfer_type: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query historical learning data for predictions
        Efficient single-partition query

        Args:
            transfer_type: Type of transfer
            limit: Maximum number of items to return

        Returns:
            List of learning data items
        """
        try:
            response = self.agent_learning_table.query(
                KeyConditionExpression=Key('transferType').eq(transfer_type),
                ScanIndexForward=False,  # DESC order by timestamp
                Limit=limit
            )
            
            items = response.get('Items', [])
            
            logger.info(f"Retrieved {len(items)} learning data items for {transfer_type}")
            
            return items
            
        except ClientError as e:
            logger.error(f"Error querying learning data: {str(e)}", exc_info=True)
            return []

    # User Context Operations

    @xray_recorder.capture('load_user_context')
    async def load_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Load user context from DynamoDB
        Partition key: userId

        Args:
            user_id: User identifier

        Returns:
            Dict containing user context
        """
        try:
            response = self.user_context_table.get_item(
                Key={'user_id': user_id}
            )
            
            if 'Item' in response:
                item = response['Item']
                
                # Parse JSON fields
                if 'conversationHistory' in item:
                    item['conversation_history'] = json.loads(item['conversationHistory'])
                if 'preferences' in item:
                    item['preferences'] = json.loads(item['preferences'])
                
                logger.info(f"Loaded context for user {user_id}")
                
                return item
            else:
                # Return default context
                return {
                    'user_id': user_id,
                    'conversation_history': [],
                    'preferences': {},
                    'created_at': datetime.utcnow().isoformat()
                }
            
        except ClientError as e:
            logger.error(f"Error loading user context: {str(e)}", exc_info=True)
            return {
                'user_id': user_id,
                'conversation_history': [],
                'preferences': {}
            }

    @xray_recorder.capture('store_user_context')
    async def store_user_context(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store user context in DynamoDB

        Args:
            user_id: User identifier
            context: User context data

        Returns:
            Dict containing result
        """
        try:
            item = {
                'userId': user_id,
                'conversationHistory': json.dumps(context.get('conversation_history', [])),
                'preferences': json.dumps(context.get('preferences', {})),
                'lastInteraction': context.get('last_interaction', datetime.utcnow().isoformat()),
                'updatedAt': datetime.utcnow().isoformat()
            }
            
            self.user_context_table.put_item(Item=item)
            
            logger.info(f"Stored context for user {user_id}")
            
            return {
                'success': True
            }
            
        except ClientError as e:
            logger.error(f"Error storing user context: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    # S3 File Cache Operations

    @xray_recorder.capture('cache_s3_metadata')
    async def cache_s3_metadata(
        self,
        bucket_name: str,
        file_key: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cache S3 file metadata (24-hour TTL)
        Partition key: bucketName, Sort key: fileKey

        Args:
            bucket_name: S3 bucket name
            file_key: S3 object key
            metadata: File metadata

        Returns:
            Dict containing result
        """
        try:
            ttl = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
            
            item = {
                'bucketName': bucket_name,
                'fileKey': file_key,
                'metadata': json.dumps(metadata),
                'cachedAt': datetime.utcnow().isoformat(),
                'ttl': ttl
            }
            
            self.s3_file_cache_table.put_item(Item=item)
            
            logger.info(f"Cached metadata for {bucket_name}/{file_key}")
            
            return {
                'success': True
            }
            
        except ClientError as e:
            logger.error(f"Error caching S3 metadata: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    @xray_recorder.capture('get_cached_s3_metadata')
    async def get_cached_s3_metadata(
        self,
        bucket_name: str,
        file_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached S3 file metadata

        Args:
            bucket_name: S3 bucket name
            file_key: S3 object key

        Returns:
            Cached metadata or None
        """
        try:
            response = self.s3_file_cache_table.get_item(
                Key={'bucketName': bucket_name, 'fileKey': file_key}
            )
            
            if 'Item' in response:
                item = response['Item']
                metadata = json.loads(item['metadata'])
                
                logger.info(f"Cache hit for {bucket_name}/{file_key}")
                
                return metadata
            else:
                logger.info(f"Cache miss for {bucket_name}/{file_key}")
                return None
            
        except ClientError as e:
            logger.error(f"Error getting cached metadata: {str(e)}", exc_info=True)
            return None

    # Active Sessions Operations

    @xray_recorder.capture('store_active_session')
    async def store_active_session(
        self,
        session_id: str,
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Store active SSO session (1-hour TTL)
        Partition key: sessionId

        Args:
            session_id: Session identifier
            session_data: Session data including credentials

        Returns:
            Dict containing result
        """
        try:
            ttl = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
            
            item = {
                'sessionId': session_id,
                'userId': session_data.get('user_id'),
                'credentials': json.dumps(session_data.get('credentials', {})),
                'createdAt': datetime.utcnow().isoformat(),
                'expiresAt': session_data.get('expires_at'),
                'ttl': ttl
            }
            
            self.active_sessions_table.put_item(Item=item)
            
            logger.info(f"Stored active session {session_id}")
            
            return {
                'success': True
            }
            
        except ClientError as e:
            logger.error(f"Error storing active session: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    @xray_recorder.capture('get_active_session')
    async def get_active_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get active SSO session

        Args:
            session_id: Session identifier

        Returns:
            Session data or None
        """
        try:
            response = self.active_sessions_table.get_item(
                Key={'sessionId': session_id}
            )
            
            if 'Item' in response:
                item = response['Item']
                item['credentials'] = json.loads(item['credentials'])
                
                logger.info(f"Retrieved active session {session_id}")
                
                return item
            else:
                return None
            
        except ClientError as e:
            logger.error(f"Error getting active session: {str(e)}", exc_info=True)
            return None

    @xray_recorder.capture('delete_active_session')
    async def delete_active_session(self, session_id: str) -> Dict[str, Any]:
        """
        Delete active SSO session (for logout)

        Args:
            session_id: Session identifier

        Returns:
            Dict containing result
        """
        try:
            self.active_sessions_table.delete_item(
                Key={'sessionId': session_id}
            )
            
            logger.info(f"Deleted active session {session_id}")
            
            return {
                'success': True
            }
            
        except ClientError as e:
            logger.error(f"Error deleting active session: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    # Utility Methods

    def _generate_id(self) -> str:
        """Generate unique identifier"""
        import uuid
        return str(uuid.uuid4())
