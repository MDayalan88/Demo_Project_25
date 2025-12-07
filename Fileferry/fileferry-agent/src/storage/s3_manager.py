"""
S3 Manager for FileFerry Agent
Handles S3 operations with caching and optimization
"""

import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

from src.utils.logger import get_logger

logger = get_logger(__name__)


class S3Manager:
    """
    Manages S3 operations for FileFerry
    Provides caching, batch operations, and optimized access
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize S3 Manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.region = config.get('aws', {}).get('region', 'us-east-1')
        
        # Initialize S3 client
        self.s3_client = boto3.client('s3', region_name=self.region)
        
        # Cache for bucket metadata
        self._bucket_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(minutes=5)
        
        logger.info(f"✅ S3Manager initialized for region: {self.region}")
    
    async def list_buckets(
        self, 
        region_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all S3 buckets
        
        Args:
            region_filter: Optional region filter
            
        Returns:
            List of bucket information
        """
        try:
            logger.info("Listing S3 buckets")
            
            response = self.s3_client.list_buckets()
            buckets = response.get('Buckets', [])
            
            bucket_list = []
            for bucket in buckets:
                bucket_info = {
                    'name': bucket['Name'],
                    'creation_date': bucket['CreationDate'].isoformat()
                }
                
                # Get bucket region if filter specified
                if region_filter:
                    try:
                        location = self.s3_client.get_bucket_location(
                            Bucket=bucket['Name']
                        )
                        bucket_region = location.get('LocationConstraint') or 'us-east-1'
                        
                        if bucket_region == region_filter:
                            bucket_info['region'] = bucket_region
                            bucket_list.append(bucket_info)
                    except Exception as e:
                        logger.warning(
                            f"Could not get location for bucket {bucket['Name']}: {str(e)}"
                        )
                else:
                    bucket_list.append(bucket_info)
            
            logger.info(f"Found {len(bucket_list)} buckets")
            return bucket_list
            
        except ClientError as e:
            logger.error(f"Error listing buckets: {str(e)}")
            raise
    
    async def list_objects(
        self,
        bucket_name: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        continuation_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List objects in a bucket
        
        Args:
            bucket_name: Bucket name
            prefix: Optional prefix filter
            max_keys: Maximum number of keys to return
            continuation_token: Token for pagination
            
        Returns:
            Dictionary with objects and pagination info
        """
        try:
            logger.info(
                f"Listing objects in bucket: {bucket_name}",
                extra={"prefix": prefix}
            )
            
            params = {
                'Bucket': bucket_name,
                'MaxKeys': max_keys
            }
            
            if prefix:
                params['Prefix'] = prefix
            
            if continuation_token:
                params['ContinuationToken'] = continuation_token
            
            response = self.s3_client.list_objects_v2(**params)
            
            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj.get('ETag', '').strip('"'),
                    'storage_class': obj.get('StorageClass', 'STANDARD')
                })
            
            result = {
                'objects': objects,
                'count': len(objects),
                'is_truncated': response.get('IsTruncated', False)
            }
            
            if response.get('NextContinuationToken'):
                result['next_token'] = response['NextContinuationToken']
            
            logger.info(
                f"Found {len(objects)} objects in bucket {bucket_name}"
            )
            
            return result
            
        except ClientError as e:
            logger.error(
                f"Error listing objects in bucket {bucket_name}: {str(e)}"
            )
            raise
    
    async def get_object_metadata(
        self,
        bucket_name: str,
        object_key: str
    ) -> Dict[str, Any]:
        """
        Get metadata for an S3 object
        
        Args:
            bucket_name: Bucket name
            object_key: Object key
            
        Returns:
            Object metadata
        """
        try:
            logger.info(
                f"Getting metadata for: {bucket_name}/{object_key}"
            )
            
            response = self.s3_client.head_object(
                Bucket=bucket_name,
                Key=object_key
            )
            
            metadata = {
                'bucket': bucket_name,
                'key': object_key,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'].isoformat(),
                'content_type': response.get('ContentType', 'unknown'),
                'etag': response.get('ETag', '').strip('"'),
                'storage_class': response.get('StorageClass', 'STANDARD'),
                'encryption': response.get('ServerSideEncryption'),
                'version_id': response.get('VersionId'),
                'metadata': response.get('Metadata', {})
            }
            
            return metadata
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"Object not found: {bucket_name}/{object_key}")
                raise FileNotFoundError(
                    f"Object {object_key} not found in bucket {bucket_name}"
                )
            else:
                logger.error(
                    f"Error getting metadata for {bucket_name}/{object_key}: {str(e)}"
                )
                raise
    
    async def get_object_size(
        self,
        bucket_name: str,
        object_key: str
    ) -> int:
        """
        Get size of an S3 object
        
        Args:
            bucket_name: Bucket name
            object_key: Object key
            
        Returns:
            Object size in bytes
        """
        try:
            metadata = await self.get_object_metadata(bucket_name, object_key)
            return metadata['size']
        except Exception as e:
            logger.error(f"Error getting object size: {str(e)}")
            raise
    
    async def check_object_exists(
        self,
        bucket_name: str,
        object_key: str
    ) -> bool:
        """
        Check if an object exists in S3
        
        Args:
            bucket_name: Bucket name
            object_key: Object key
            
        Returns:
            True if object exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=bucket_name,
                Key=object_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"Error checking object existence: {str(e)}")
                raise
    
    async def generate_presigned_url(
        self,
        bucket_name: str,
        object_key: str,
        expiration: int = 3600,
        http_method: str = 'get_object'
    ) -> str:
        """
        Generate a presigned URL for S3 object access
        
        Args:
            bucket_name: Bucket name
            object_key: Object key
            expiration: URL expiration in seconds (default: 1 hour)
            http_method: HTTP method (get_object, put_object)
            
        Returns:
            Presigned URL
        """
        try:
            logger.info(
                f"Generating presigned URL for: {bucket_name}/{object_key}"
            )
            
            url = self.s3_client.generate_presigned_url(
                ClientMethod=http_method,
                Params={
                    'Bucket': bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            
            return url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise
    
    async def copy_object(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Copy an object within S3
        
        Args:
            source_bucket: Source bucket name
            source_key: Source object key
            dest_bucket: Destination bucket name
            dest_key: Destination object key
            metadata: Optional metadata to set
            
        Returns:
            Copy result
        """
        try:
            logger.info(
                f"Copying object: {source_bucket}/{source_key} → {dest_bucket}/{dest_key}"
            )
            
            copy_source = {
                'Bucket': source_bucket,
                'Key': source_key
            }
            
            params = {
                'CopySource': copy_source,
                'Bucket': dest_bucket,
                'Key': dest_key
            }
            
            if metadata:
                params['Metadata'] = metadata
                params['MetadataDirective'] = 'REPLACE'
            
            response = self.s3_client.copy_object(**params)
            
            return {
                'status': 'success',
                'etag': response.get('CopyObjectResult', {}).get('ETag', '').strip('"'),
                'last_modified': response.get('CopyObjectResult', {}).get('LastModified')
            }
            
        except ClientError as e:
            logger.error(f"Error copying object: {str(e)}")
            raise
    
    async def delete_object(
        self,
        bucket_name: str,
        object_key: str
    ) -> Dict[str, Any]:
        """
        Delete an object from S3
        
        Args:
            bucket_name: Bucket name
            object_key: Object key
            
        Returns:
            Deletion result
        """
        try:
            logger.info(f"Deleting object: {bucket_name}/{object_key}")
            
            self.s3_client.delete_object(
                Bucket=bucket_name,
                Key=object_key
            )
            
            return {
                'status': 'success',
                'message': f'Deleted {object_key} from {bucket_name}'
            }
            
        except ClientError as e:
            logger.error(f"Error deleting object: {str(e)}")
            raise
    
    async def get_bucket_region(self, bucket_name: str) -> str:
        """
        Get the region of an S3 bucket
        
        Args:
            bucket_name: Bucket name
            
        Returns:
            AWS region
        """
        try:
            # Check cache first
            if bucket_name in self._bucket_cache:
                cache_entry = self._bucket_cache[bucket_name]
                if datetime.now() - cache_entry['timestamp'] < self._cache_ttl:
                    return cache_entry['region']
            
            # Get from AWS
            response = self.s3_client.get_bucket_location(Bucket=bucket_name)
            region = response.get('LocationConstraint') or 'us-east-1'
            
            # Cache the result
            self._bucket_cache[bucket_name] = {
                'region': region,
                'timestamp': datetime.now()
            }
            
            return region
            
        except ClientError as e:
            logger.error(f"Error getting bucket region: {str(e)}")
            raise
    
    def get_s3_client(self, region: Optional[str] = None) -> Any:
        """
        Get an S3 client for a specific region
        
        Args:
            region: AWS region (uses default if not specified)
            
        Returns:
            Boto3 S3 client
        """
        target_region = region or self.region
        
        if target_region == self.region:
            return self.s3_client
        
        return boto3.client('s3', region_name=target_region)