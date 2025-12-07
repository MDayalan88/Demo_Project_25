"""
Agent Tools for FileFerry AI Agent
Provides S3, SFTP, and transfer orchestration capabilities
"""

from typing import Dict, Any, List, Optional
import boto3
from datetime import datetime

from src.storage.s3_manager import S3Manager
from src.storage.azure_blob_manager import AzureBlobManager
from src.storage.dynamodb_manager import DynamoDBManager
from src.handlers.transfer_handler import TransferHandler
from src.handlers.sso_handler import SSOHandler
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AgentTools:
    """
    Unified tool interface for FileFerry AI Agent
    Provides S3, SFTP, and transfer capabilities
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize agent tools
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Initialize handlers
        logger.info("Initializing agent tools...")
        
        # ✅ Initialize SSO handler first (required by TransferHandler)
        self.sso_handler = SSOHandler(config)
        
        # ✅ Pass sso_handler to TransferHandler
        self.transfer_handler = TransferHandler(config, self.sso_handler)
        
        # Initialize storage managers for both AWS and Azure
        self.s3_manager = S3Manager(config)
        self.azure_blob_manager = AzureBlobManager(config)
        self.dynamodb = DynamoDBManager(config)
        
        logger.info("✅ Agent tools initialized (AWS + Azure support)")
    
    async def list_s3_buckets(
        self, 
        user_id: str,
        region: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List S3 buckets accessible to the user
        
        Args:
            user_id: User identifier
            region: Optional AWS region filter
            
        Returns:
            List of bucket information dictionaries
        """
        try:
            logger.info(f"Listing S3 buckets for user: {user_id}")
            
            # Get temporary credentials via SSO
            credentials = await self.sso_handler.get_temporary_credentials(
                user_id=user_id,
                account_id=self.config['aws']['account_id'],
                role_name=self.config['aws']['sso']['role_name']
            )
            
            # Create S3 client with temporary credentials
            s3_client = boto3.client(
                's3',
                region_name=region or self.config['aws']['region'],
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
            
            # List buckets
            response = s3_client.list_buckets()
            
            buckets = []
            for bucket in response.get('Buckets', []):
                bucket_info = {
                    'name': bucket['Name'],
                    'creation_date': bucket['CreationDate'].isoformat()
                }
                
                # Get bucket region
                try:
                    location = s3_client.get_bucket_location(Bucket=bucket['Name'])
                    bucket_info['region'] = location.get('LocationConstraint') or 'us-east-1'
                except Exception:
                    bucket_info['region'] = 'unknown'
                
                buckets.append(bucket_info)
            
            logger.info(f"Found {len(buckets)} buckets for user {user_id}")
            return buckets
            
        except Exception as e:
            logger.error(f"Error listing S3 buckets: {str(e)}", extra={"user_id": user_id})
            raise
    
    async def list_files_in_bucket(
        self,
        user_id: str,
        bucket_name: str,
        prefix: str = "",
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List files in an S3 bucket
        
        Args:
            user_id: User identifier
            bucket_name: S3 bucket name
            prefix: Optional prefix filter
            max_results: Maximum number of results
            
        Returns:
            List of file information dictionaries
        """
        try:
            logger.info(
                f"Listing files in bucket: {bucket_name}",
                extra={"user_id": user_id, "prefix": prefix}
            )
            
            # Get temporary credentials
            credentials = await self.sso_handler.get_temporary_credentials(
                user_id=user_id,
                account_id=self.config['aws']['account_id'],
                role_name=self.config['aws']['sso']['role_name']
            )
            
            # Create S3 client
            s3_client = boto3.client(
                's3',
                region_name=self.config['aws']['region'],
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
            
            # List objects
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=max_results
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag'].strip('"')
                })
            
            logger.info(
                f"Found {len(files)} files in bucket {bucket_name}",
                extra={"user_id": user_id}
            )
            
            return files
            
        except Exception as e:
            logger.error(
                f"Error listing files in bucket: {str(e)}",
                extra={"user_id": user_id, "bucket": bucket_name}
            )
            raise
    
    async def get_file_details(
        self,
        user_id: str,
        bucket_name: str,
        file_key: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about a file
        
        Args:
            user_id: User identifier
            bucket_name: S3 bucket name
            file_key: S3 object key
            
        Returns:
            File details dictionary
        """
        try:
            logger.info(
                f"Getting file details: {file_key}",
                extra={"user_id": user_id, "bucket": bucket_name}
            )
            
            # Get temporary credentials
            credentials = await self.sso_handler.get_temporary_credentials(
                user_id=user_id,
                account_id=self.config['aws']['account_id'],
                role_name=self.config['aws']['sso']['role_name']
            )
            
            # Create S3 client
            s3_client = boto3.client(
                's3',
                region_name=self.config['aws']['region'],
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
            
            # Get object metadata
            response = s3_client.head_object(
                Bucket=bucket_name,
                Key=file_key
            )
            
            details = {
                'bucket': bucket_name,
                'key': file_key,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'].isoformat(),
                'content_type': response.get('ContentType', 'unknown'),
                'etag': response['ETag'].strip('"'),
                'metadata': response.get('Metadata', {})
            }
            
            # Add storage class if available
            if 'StorageClass' in response:
                details['storage_class'] = response['StorageClass']
            
            return details
            
        except Exception as e:
            logger.error(
                f"Error getting file details: {str(e)}",
                extra={"user_id": user_id, "bucket": bucket_name, "key": file_key}
            )
            raise
    
    async def initiate_transfer(
        self,
        user_id: str,
        source_bucket: str,
        source_key: str,
        destination_host: str,
        destination_path: str,
        destination_type: str = "sftp",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initiate a file transfer from S3 to SFTP/FTP
        
        Args:
            user_id: User identifier
            source_bucket: Source S3 bucket
            source_key: Source S3 object key
            destination_host: Destination SFTP/FTP host
            destination_path: Destination file path
            destination_type: Transfer type ('sftp' or 'ftp')
            options: Optional transfer options
            
        Returns:
            Transfer request information
        """
        try:
            logger.info(
                f"Initiating transfer: {source_bucket}/{source_key} → {destination_host}",
                extra={"user_id": user_id}
            )
            
            # Create transfer request
            transfer_request = await self.transfer_handler.create_transfer_request(
                user_id=user_id,
                source_bucket=source_bucket,
                source_key=source_key,
                destination_host=destination_host,
                destination_path=destination_path,
                destination_type=destination_type,
                options=options or {}
            )
            
            logger.info(
                f"Transfer initiated: {transfer_request['transfer_id']}",
                extra={"user_id": user_id, "transfer_id": transfer_request['transfer_id']}
            )
            
            return transfer_request
            
        except Exception as e:
            logger.error(
                f"Error initiating transfer: {str(e)}",
                extra={"user_id": user_id}
            )
            raise
    
    async def get_transfer_status(
        self,
        user_id: str,
        transfer_id: str
    ) -> Dict[str, Any]:
        """
        Get status of a transfer
        
        Args:
            user_id: User identifier
            transfer_id: Transfer request ID
            
        Returns:
            Transfer status information
        """
        try:
            # Get transfer request from DynamoDB
            response = self.dynamodb.get_item(
                table_name=self.config['aws']['dynamodb']['transfer_requests_table'],
                key={'transfer_id': transfer_id}
            )
            
            if not response:
                raise ValueError(f"Transfer not found: {transfer_id}")
            
            # Verify user has access
            if response.get('user_id') != user_id:
                raise PermissionError(f"User {user_id} does not have access to transfer {transfer_id}")
            
            return response
            
        except Exception as e:
            logger.error(
                f"Error getting transfer status: {str(e)}",
                extra={"user_id": user_id, "transfer_id": transfer_id}
            )
            raise
    
    async def list_user_transfers(
        self,
        user_id: str,
        limit: int = 10,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List transfers for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            status_filter: Optional status filter (pending, running, completed, failed)
            
        Returns:
            List of transfer information
        """
        try:
            # Query DynamoDB for user's transfers
            response = self.dynamodb.query_items(
                table_name=self.config['aws']['dynamodb']['transfer_requests_table'],
                index_name='user_id-index',
                key_condition='user_id = :user_id',
                expression_values={':user_id': user_id},
                limit=limit,
                scan_index_forward=False  # Most recent first
            )
            
            transfers = response.get('Items', [])
            
            # Apply status filter if provided
            if status_filter:
                transfers = [t for t in transfers if t.get('status') == status_filter]
            
            return transfers
            
        except Exception as e:
            logger.error(
                f"Error listing user transfers: {str(e)}",
                extra={"user_id": user_id}
            )
            raise
    
    # ============================================
    # Azure Blob Storage Methods
    # ============================================
    
    async def list_azure_containers(
        self, 
        user_id: str,
        name_prefix: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List Azure Storage containers (equivalent to S3 buckets)
        
        Args:
            user_id: User identifier
            name_prefix: Optional container name prefix filter
            
        Returns:
            List of container information dictionaries
        """
        try:
            logger.info(f"Listing Azure containers for user: {user_id}")
            
            # List containers using Azure Blob Manager
            containers = await self.azure_blob_manager.list_containers(
                name_prefix=name_prefix
            )
            
            logger.info(f"Found {len(containers)} containers for user {user_id}")
            return containers
            
        except Exception as e:
            logger.error(f"Error listing Azure containers: {str(e)}", extra={"user_id": user_id})
            raise
    
    async def list_azure_blobs(
        self,
        user_id: str,
        container_name: str,
        prefix: Optional[str] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List blobs in an Azure container (equivalent to S3 objects)
        
        Args:
            user_id: User identifier
            container_name: Azure container name
            prefix: Optional prefix filter
            max_results: Maximum number of results
            
        Returns:
            List of blob information dictionaries
        """
        try:
            logger.info(
                f"Listing blobs in container: {container_name}",
                extra={"user_id": user_id, "prefix": prefix}
            )
            
            # List blobs using Azure Blob Manager
            result = await self.azure_blob_manager.list_blobs(
                container_name=container_name,
                prefix=prefix,
                max_results=max_results
            )
            
            blobs = result.get('blobs', [])
            
            logger.info(
                f"Found {len(blobs)} blobs in container {container_name}",
                extra={"user_id": user_id}
            )
            
            return blobs
            
        except Exception as e:
            logger.error(
                f"Error listing blobs in container: {str(e)}",
                extra={"user_id": user_id, "container": container_name}
            )
            raise
    
    async def get_azure_blob_metadata(
        self,
        user_id: str,
        container_name: str,
        blob_name: str
    ) -> Dict[str, Any]:
        """
        Get detailed metadata for an Azure blob (equivalent to S3 object)
        
        Args:
            user_id: User identifier
            container_name: Azure container name
            blob_name: Blob name
            
        Returns:
            Blob metadata dictionary
        """
        try:
            logger.info(
                f"Getting Azure blob metadata: {container_name}/{blob_name}",
                extra={"user_id": user_id}
            )
            
            # Get blob metadata using Azure Blob Manager
            metadata = await self.azure_blob_manager.get_blob_metadata(
                container_name=container_name,
                blob_name=blob_name
            )
            
            logger.info(
                f"Retrieved metadata for blob: {blob_name}",
                extra={"user_id": user_id, "size": metadata.get('size')}
            )
            
            return metadata
            
        except Exception as e:
            logger.error(
                f"Error getting Azure blob metadata: {str(e)}",
                extra={"user_id": user_id, "container": container_name, "blob": blob_name}
            )
            raise