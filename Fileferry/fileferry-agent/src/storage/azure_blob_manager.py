"""
Azure Blob Storage Manager for FileFerry Agent
Handles Azure Blob Storage operations with support for Azurite emulator
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobClient
from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential

from src.utils.logger import get_logger

logger = get_logger(__name__)


class AzureBlobManager:
    """
    Manages Azure Blob Storage operations for FileFerry
    Supports both Azurite emulator (local dev) and production Azure
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Azure Blob Manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        azure_config = config.get('azure', {})
        
        # Determine if using Azurite emulator, production, or mock mode
        self.use_emulator = azure_config.get('use_emulator', True)
        self.use_mock = azure_config.get('use_mock', False)
        
        # Mock mode - simulate Azure without any connection
        if self.use_mock:
            logger.info("🎭 Using MOCK mode - simulating Azure Blob Storage (no Azurite needed)")
            self.blob_service_client = None
            self._mock_data = {
                'containers': {},
                'blobs': {}
            }
            logger.info("✅ AzureBlobManager initialized in MOCK mode")
            return
        
        if self.use_emulator:
            # Azurite emulator connection string (local development)
            self.connection_string = (
                "DefaultEndpointsProtocol=http;"
                "AccountName=devstoreaccount1;"
                "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
                "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
            )
            logger.info("🔧 Using Azurite emulator for local development")
        else:
            # Production Azure connection
            self.connection_string = azure_config.get('connection_string')
            self.account_name = azure_config.get('account_name')
            self.account_url = azure_config.get('account_url')
            logger.info(f"☁️ Using production Azure Storage: {self.account_name}")
        
        # Initialize BlobServiceClient
        try:
            if self.connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    self.connection_string
                )
            elif self.account_url:
                # Use managed identity or DefaultAzureCredential
                credential = DefaultAzureCredential()
                self.blob_service_client = BlobServiceClient(
                    account_url=self.account_url,
                    credential=credential
                )
            else:
                raise ValueError("Azure connection string or account URL required")
            
            logger.info("✅ AzureBlobManager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AzureBlobManager: {str(e)}")
            raise
        
        # Cache for container metadata
        self._container_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(minutes=5)
    
    async def list_containers(
        self,
        name_prefix: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all containers (equivalent to S3 buckets)
        
        Args:
            name_prefix: Optional prefix filter
            
        Returns:
            List of container information
        """
        # Mock mode
        if self.use_mock:
            container_list = [
                {
                    'name': name,
                    'last_modified': datetime.now().isoformat(),
                    'metadata': data.get('metadata', {})
                }
                for name, data in self._mock_data['containers'].items()
                if not name_prefix or name.startswith(name_prefix)
            ]
            logger.info(f"[MOCK] Found {len(container_list)} containers")
            return container_list
        
        try:
            logger.info("Listing Azure Storage containers")
            
            containers = self.blob_service_client.list_containers(
                name_starts_with=name_prefix
            )
            
            container_list = []
            for container in containers:
                container_info = {
                    'name': container['name'],
                    'last_modified': container['last_modified'].isoformat(),
                    'metadata': container.get('metadata', {})
                }
                container_list.append(container_info)
            
            logger.info(f"Found {len(container_list)} containers")
            return container_list
            
        except AzureError as e:
            logger.error(f"Error listing containers: {str(e)}")
            raise
    
    async def list_blobs(
        self,
        container_name: str,
        prefix: Optional[str] = None,
        max_results: int = 1000
    ) -> Dict[str, Any]:
        """
        List blobs in a container (equivalent to S3 objects)
        
        Args:
            container_name: Container name
            prefix: Optional prefix filter
            max_results: Maximum number of blobs to return
            
        Returns:
            Dictionary with blobs and metadata
        """
        # Mock mode
        if self.use_mock:
            container = self._mock_data['containers'].get(container_name, {})
            blobs_data = container.get('blobs', {})
            blobs = [
                blob_info
                for blob_name, blob_info in blobs_data.items()
                if not prefix or blob_name.startswith(prefix)
            ]
            result = {
                'blobs': blobs,
                'count': len(blobs),
                'container': container_name
            }
            logger.info(f"[MOCK] Found {len(blobs)} blobs in container {container_name}")
            return result
        
        try:
            logger.info(
                f"Listing blobs in container: {container_name}",
                extra={"prefix": prefix}
            )
            
            container_client = self.blob_service_client.get_container_client(
                container_name
            )
            
            blob_list = container_client.list_blobs(
                name_starts_with=prefix,
                results_per_page=max_results
            )
            
            blobs = []
            for blob in blob_list:
                blobs.append({
                    'name': blob.name,
                    'size': blob.size,
                    'last_modified': blob.last_modified.isoformat(),
                    'content_type': blob.content_settings.content_type if blob.content_settings else 'unknown',
                    'etag': blob.etag.strip('"') if blob.etag else '',
                    'blob_type': blob.blob_type,
                    'metadata': blob.metadata or {}
                })
            
            result = {
                'blobs': blobs,
                'count': len(blobs),
                'container': container_name
            }
            
            logger.info(
                f"Found {len(blobs)} blobs in container {container_name}"
            )
            
            return result
            
        except ResourceNotFoundError:
            logger.error(f"Container not found: {container_name}")
            raise
        except AzureError as e:
            logger.error(
                f"Error listing blobs in container {container_name}: {str(e)}"
            )
            raise
    
    async def get_blob_metadata(
        self,
        container_name: str,
        blob_name: str
    ) -> Dict[str, Any]:
        """
        Get metadata for a blob (equivalent to S3 object metadata)
        
        Args:
            container_name: Container name
            blob_name: Blob name
            
        Returns:
            Blob metadata
        """
        # Mock mode
        if self.use_mock:
            container = self._mock_data['containers'].get(container_name, {})
            blob = container.get('blobs', {}).get(blob_name)
            if not blob:
                raise Exception(f"[MOCK] Blob not found: {container_name}/{blob_name}")
            metadata = {
                'container': container_name,
                'name': blob['name'],
                'size': blob['size'],
                'last_modified': blob['last_modified'],
                'content_type': blob['content_type'],
                'etag': blob['etag'],
                'blob_type': blob['blob_type'],
                'encryption_scope': None,
                'metadata': blob['metadata']
            }
            logger.info(f"[MOCK] Retrieved metadata for blob: {blob_name}")
            return metadata
        
        try:
            logger.info(
                f"Getting metadata for: {container_name}/{blob_name}"
            )
            
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            properties = blob_client.get_blob_properties()
            
            metadata = {
                'container': container_name,
                'name': blob_name,
                'size': properties.size,
                'last_modified': properties.last_modified.isoformat(),
                'content_type': properties.content_settings.content_type if properties.content_settings else 'unknown',
                'etag': properties.etag.strip('"') if properties.etag else '',
                'blob_type': properties.blob_type,
                'encryption_scope': properties.encryption_scope,
                'metadata': properties.metadata or {}
            }
            
            return metadata
            
        except ResourceNotFoundError:
            logger.error(f"Blob not found: {container_name}/{blob_name}")
            raise
        except AzureError as e:
            logger.error(
                f"Error getting metadata for {container_name}/{blob_name}: {str(e)}"
            )
            raise
    
    async def upload_blob(
        self,
        container_name: str,
        blob_name: str,
        data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload data as a blob
        
        Args:
            container_name: Container name
            blob_name: Blob name
            data: Data to upload
            content_type: Content type
            metadata: Optional metadata
            
        Returns:
            Upload result
        """
        # Mock mode
        if self.use_mock:
            if container_name not in self._mock_data['containers']:
                self._mock_data['containers'][container_name] = {'metadata': {}, 'blobs': {}}
            
            blob_info = {
                'name': blob_name,
                'size': len(data),
                'last_modified': datetime.now().isoformat(),
                'content_type': content_type or 'application/octet-stream',
                'etag': f'mock-etag-{hash(blob_name)}',
                'blob_type': 'BlockBlob',
                'metadata': metadata or {},
                '_data': data
            }
            self._mock_data['containers'][container_name]['blobs'][blob_name] = blob_info
            logger.info(f"[MOCK] ✅ Blob uploaded successfully: {blob_name}")
            return {
                'container': container_name,
                'blob': blob_name,
                'size': len(data),
                'etag': blob_info['etag'],
                'last_modified': blob_info['last_modified']
            }
        
        try:
            logger.info(
                f"Uploading blob: {container_name}/{blob_name}",
                extra={"size": len(data)}
            )
            
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            # Upload blob
            result = blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings={'content_type': content_type} if content_type else None,
                metadata=metadata
            )
            
            logger.info(f"✅ Blob uploaded successfully: {blob_name}")
            
            return {
                'container': container_name,
                'blob': blob_name,
                'size': len(data),
                'etag': result.get('etag', '').strip('"'),
                'last_modified': result.get('last_modified').isoformat() if result.get('last_modified') else None
            }
            
        except AzureError as e:
            logger.error(f"Error uploading blob: {str(e)}")
            raise
    
    async def download_blob(
        self,
        container_name: str,
        blob_name: str
    ) -> bytes:
        """
        Download blob data
        
        Args:
            container_name: Container name
            blob_name: Blob name
            
        Returns:
            Blob data as bytes
        """
        # Mock mode
        if self.use_mock:
            container = self._mock_data['containers'].get(container_name, {})
            blob = container.get('blobs', {}).get(blob_name)
            if not blob:
                raise Exception(f"[MOCK] Blob not found: {container_name}/{blob_name}")
            data = blob.get('_data', b'')
            logger.info(f"[MOCK] ✅ Blob downloaded successfully: {blob_name}")
            return data
        
        try:
            logger.info(
                f"Downloading blob: {container_name}/{blob_name}"
            )
            
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            download_stream = blob_client.download_blob()
            data = download_stream.readall()
            
            logger.info(
                f"✅ Blob downloaded successfully: {blob_name}",
                extra={"size": len(data)}
            )
            
            return data
            
        except ResourceNotFoundError:
            logger.error(f"Blob not found: {container_name}/{blob_name}")
            raise
        except AzureError as e:
            logger.error(f"Error downloading blob: {str(e)}")
            raise
    
    async def delete_blob(
        self,
        container_name: str,
        blob_name: str
    ) -> bool:
        """
        Delete a blob
        
        Args:
            container_name: Container name
            blob_name: Blob name
            
        Returns:
            True if deleted successfully
        """
        try:
            logger.info(
                f"Deleting blob: {container_name}/{blob_name}"
            )
            
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            blob_client.delete_blob()
            
            logger.info(f"✅ Blob deleted successfully: {blob_name}")
            
            return True
            
        except ResourceNotFoundError:
            logger.warning(f"Blob not found (already deleted?): {container_name}/{blob_name}")
            return False
        except AzureError as e:
            logger.error(f"Error deleting blob: {str(e)}")
            raise
    
    async def create_container(
        self,
        container_name: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new container
        
        Args:
            container_name: Container name
            metadata: Optional metadata
            
        Returns:
            Container creation result
        """
        # Mock mode
        if self.use_mock:
            self._mock_data['containers'][container_name] = {
                'metadata': metadata or {},
                'blobs': {}
            }
            logger.info(f"[MOCK] ✅ Container created successfully: {container_name}")
            return {
                'name': container_name,
                'created': True
            }
        
        try:
            logger.info(f"Creating container: {container_name}")
            
            container_client = self.blob_service_client.create_container(
                name=container_name,
                metadata=metadata
            )
            
            logger.info(f"✅ Container created successfully: {container_name}")
            
            return {
                'name': container_name,
                'created': True
            }
            
        except AzureError as e:
            logger.error(f"Error creating container: {str(e)}")
            raise
    
    async def delete_container(
        self,
        container_name: str
    ) -> bool:
        """
        Delete a container
        
        Args:
            container_name: Container name
            
        Returns:
            True if deleted successfully
        """
        try:
            logger.info(f"Deleting container: {container_name}")
            
            self.blob_service_client.delete_container(container_name)
            
            logger.info(f"✅ Container deleted successfully: {container_name}")
            
            return True
            
        except ResourceNotFoundError:
            logger.warning(f"Container not found (already deleted?): {container_name}")
            return False
        except AzureError as e:
            logger.error(f"Error deleting container: {str(e)}")
            raise
