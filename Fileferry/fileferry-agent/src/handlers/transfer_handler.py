"""
Transfer Handler - Initiates and manages file transfers
Uses AWS Step Functions for orchestration
Implements S3→FTP/SFTP streaming with progress tracking
"""

import boto3
import json
import io
import hashlib
import paramiko
from ftplib import FTP, FTP_TLS
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential
from aws_xray_sdk.core import xray_recorder

from ..handlers.sso_handler import SSOHandler
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TransferHandler:
    """
    Manages file transfer execution via AWS Step Functions
    """
    
    def __init__(self, config: Dict[str, Any], sso_handler: SSOHandler):
        """
        Initialize Transfer Handler
        
        Args:
            config: Configuration dictionary
            sso_handler: SSO handler instance
        """
        self.config = config
        self.sso_handler = sso_handler
        
        region = config.get('aws', {}).get('region', 'us-east-1')
        self.sfn_client = boto3.client('stepfunctions', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        self.state_machine_arn = config.get('step_functions', {}).get('state_machine_arn')
        
        # Transfer configuration
        transfer_config = config.get('transfer', {})
        self.chunk_size = transfer_config.get('default_chunk_size', 10485760)  # 10MB
        self.max_threads = transfer_config.get('max_parallel_threads', 5)
        self.small_file_threshold = transfer_config.get('small_file_threshold', 104857600)  # 100MB
        
        # DynamoDB table for transfer tracking
        self.transfer_table_name = config.get('dynamodb', {}).get('transfer_requests_table', 'FileFerry-TransferRequests')
        
        logger.info("✅ Transfer Handler initialized")
    
    @xray_recorder.capture('initiate_transfer')
    async def initiate_transfer(
        self,
        user_id: str,
        transfer_plan: Dict[str, Any],
        servicenow_tickets: list
    ) -> Dict[str, Any]:
        """
        Initiate file transfer via Step Functions
        
        Args:
            user_id: User ID
            transfer_plan: Transfer plan from agent
            servicenow_tickets: ServiceNow ticket IDs
            
        Returns:
            Transfer initiation result
        """
        try:
            # Authenticate with SSO
            session_data = await self.sso_handler.authenticate()
            
            # Prepare Step Functions input
            execution_input = {
                'user_id': user_id,
                'transfer_plan': transfer_plan,
                'servicenow_tickets': servicenow_tickets,
                'session_data': {
                    'session_id': session_data['session_id'],
                    'region': session_data['region']
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Start Step Functions execution
            execution_name = f"transfer-{int(datetime.utcnow().timestamp() * 1000)}"
            
            response = self.sfn_client.start_execution(
                stateMachineArn=self.state_machine_arn,
                name=execution_name,
                input=json.dumps(execution_input)
            )
            
            execution_arn = response['executionArn']
            
            logger.info(f"✅ Started Step Functions execution: {execution_arn}")
            
            return {
                'status': 'success',
                'execution_arn': execution_arn,
                'execution_name': execution_name,
                'message': 'Transfer initiated successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Error initiating transfer: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @xray_recorder.capture('stream_s3_to_ftp')
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def stream_s3_to_ftp(
        self,
        bucket: str,
        key: str,
        ftp_config: Dict[str, Any],
        transfer_id: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Stream file from S3 to FTP/SFTP with chunked transfer
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            ftp_config: FTP configuration (host, port, username, password, protocol)
            transfer_id: Unique transfer ID for tracking
            progress_callback: Optional callback for progress updates
            
        Returns:
            Transfer result with status and metadata
        """
        try:
            # Get S3 object metadata
            s3_metadata = self.s3_client.head_object(Bucket=bucket, Key=key)
            file_size = s3_metadata['ContentLength']
            
            logger.info(f"📥 Starting S3→FTP transfer: {bucket}/{key} ({file_size} bytes)")
            
            # Determine transfer protocol
            protocol = ftp_config.get('protocol', 'ftp').lower()
            
            if protocol in ['sftp', 'ssh']:
                result = await self._stream_to_sftp(bucket, key, file_size, ftp_config, transfer_id, progress_callback)
            elif protocol in ['ftps', 'ftp-tls']:
                result = await self._stream_to_ftps(bucket, key, file_size, ftp_config, transfer_id, progress_callback)
            else:  # Standard FTP
                result = await self._stream_to_ftp(bucket, key, file_size, ftp_config, transfer_id, progress_callback)
            
            # Update DynamoDB with completion
            await self._update_transfer_status(transfer_id, 'completed', result)
            
            logger.info(f"✅ Transfer completed: {transfer_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Transfer failed: {str(e)}", exc_info=True)
            await self._update_transfer_status(transfer_id, 'failed', {'error': str(e)})
            raise
    
    async def _stream_to_ftp(
        self,
        bucket: str,
        key: str,
        file_size: int,
        ftp_config: Dict[str, Any],
        transfer_id: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Stream to standard FTP server"""
        
        ftp = FTP()
        ftp.connect(ftp_config['host'], ftp_config.get('port', 21))
        ftp.login(ftp_config['username'], ftp_config['password'])
        
        try:
            # Change to destination directory if specified
            if 'remote_path' in ftp_config:
                ftp.cwd(ftp_config['remote_path'])
            
            # Stream from S3 to FTP
            s3_object = self.s3_client.get_object(Bucket=bucket, Key=key)
            s3_stream = s3_object['Body']
            
            bytes_transferred = 0
            checksum = hashlib.md5()
            
            # Determine remote filename
            remote_filename = ftp_config.get('remote_filename', key.split('/')[-1])
            
            def callback(data):
                nonlocal bytes_transferred
                bytes_transferred += len(data)
                checksum.update(data)
                
                if progress_callback:
                    progress_callback(bytes_transferred, file_size)
                
                # Update DynamoDB every 10MB
                if bytes_transferred % (10 * 1024 * 1024) == 0:
                    self._update_transfer_progress(transfer_id, bytes_transferred, file_size)
            
            # Upload with chunked reading
            ftp.storbinary(f'STOR {remote_filename}', s3_stream, blocksize=self.chunk_size, callback=lambda data: callback(data))
            
            ftp.quit()
            
            return {
                'status': 'success',
                'bytes_transferred': bytes_transferred,
                'md5_checksum': checksum.hexdigest(),
                'remote_path': f"{ftp_config.get('remote_path', '/')}/{remote_filename}"
            }
            
        except Exception as e:
            ftp.quit()
            raise
    
    async def _stream_to_sftp(
        self,
        bucket: str,
        key: str,
        file_size: int,
        ftp_config: Dict[str, Any],
        transfer_id: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Stream to SFTP server using Paramiko"""
        
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh.connect(
            hostname=ftp_config['host'],
            port=ftp_config.get('port', 22),
            username=ftp_config['username'],
            password=ftp_config.get('password'),
            key_filename=ftp_config.get('private_key_path')
        )
        
        sftp = ssh.open_sftp()
        
        try:
            # Change to remote directory
            if 'remote_path' in ftp_config:
                try:
                    sftp.chdir(ftp_config['remote_path'])
                except IOError:
                    # Create directory if it doesn't exist
                    sftp.mkdir(ftp_config['remote_path'])
                    sftp.chdir(ftp_config['remote_path'])
            
            # Stream from S3
            s3_object = self.s3_client.get_object(Bucket=bucket, Key=key)
            s3_stream = s3_object['Body']
            
            remote_filename = ftp_config.get('remote_filename', key.split('/')[-1])
            remote_file_path = f"{ftp_config.get('remote_path', '.')}/{remote_filename}"
            
            bytes_transferred = 0
            checksum = hashlib.md5()
            
            # Open remote file for writing
            with sftp.open(remote_file_path, 'wb') as remote_file:
                # Read and write in chunks
                while True:
                    chunk = s3_stream.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    remote_file.write(chunk)
                    bytes_transferred += len(chunk)
                    checksum.update(chunk)
                    
                    if progress_callback:
                        progress_callback(bytes_transferred, file_size)
                    
                    # Update progress every 10MB
                    if bytes_transferred % (10 * 1024 * 1024) == 0:
                        self._update_transfer_progress(transfer_id, bytes_transferred, file_size)
            
            sftp.close()
            ssh.close()
            
            return {
                'status': 'success',
                'bytes_transferred': bytes_transferred,
                'md5_checksum': checksum.hexdigest(),
                'remote_path': remote_file_path
            }
            
        except Exception as e:
            sftp.close()
            ssh.close()
            raise
    
    async def _stream_to_ftps(
        self,
        bucket: str,
        key: str,
        file_size: int,
        ftp_config: Dict[str, Any],
        transfer_id: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Stream to FTPS (FTP over TLS) server"""
        
        ftps = FTP_TLS()
        ftps.connect(ftp_config['host'], ftp_config.get('port', 21))
        ftps.login(ftp_config['username'], ftp_config['password'])
        ftps.prot_p()  # Enable secure data connection
        
        try:
            if 'remote_path' in ftp_config:
                ftps.cwd(ftp_config['remote_path'])
            
            s3_object = self.s3_client.get_object(Bucket=bucket, Key=key)
            s3_stream = s3_object['Body']
            
            bytes_transferred = 0
            checksum = hashlib.md5()
            remote_filename = ftp_config.get('remote_filename', key.split('/')[-1])
            
            def callback(data):
                nonlocal bytes_transferred
                bytes_transferred += len(data)
                checksum.update(data)
                
                if progress_callback:
                    progress_callback(bytes_transferred, file_size)
                
                if bytes_transferred % (10 * 1024 * 1024) == 0:
                    self._update_transfer_progress(transfer_id, bytes_transferred, file_size)
            
            ftps.storbinary(f'STOR {remote_filename}', s3_stream, blocksize=self.chunk_size, callback=lambda data: callback(data))
            
            ftps.quit()
            
            return {
                'status': 'success',
                'bytes_transferred': bytes_transferred,
                'md5_checksum': checksum.hexdigest(),
                'remote_path': f"{ftp_config.get('remote_path', '/')}/{remote_filename}"
            }
            
        except Exception as e:
            ftps.quit()
            raise
    
    async def execute_parallel_transfer(
        self,
        files: list,
        ftp_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute multiple file transfers in parallel
        
        Args:
            files: List of file dictionaries with 'bucket', 'key', 'transfer_id'
            ftp_config: FTP configuration
            
        Returns:
            Aggregated transfer results
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {
                executor.submit(
                    self.stream_s3_to_ftp,
                    file['bucket'],
                    file['key'],
                    ftp_config,
                    file['transfer_id']
                ): file for file in files
            }
            
            for future in as_completed(futures):
                file = futures[future]
                try:
                    result = future.result()
                    results.append({
                        'file': file['key'],
                        'status': 'success',
                        'result': result
                    })
                    logger.info(f"✅ Parallel transfer completed: {file['key']}")
                except Exception as e:
                    results.append({
                        'file': file['key'],
                        'status': 'failed',
                        'error': str(e)
                    })
                    logger.error(f"❌ Parallel transfer failed: {file['key']} - {str(e)}")
        
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = len(results) - successful
        
        return {
            'total_files': len(files),
            'successful': successful,
            'failed': failed,
            'results': results
        }
    
    async def validate_transfer_completion(
        self,
        transfer_id: str,
        expected_checksum: str,
        ftp_config: Dict[str, Any]
    ) -> bool:
        """
        Validate transfer completion by comparing checksums
        
        Args:
            transfer_id: Transfer ID
            expected_checksum: Expected MD5 checksum
            ftp_config: FTP configuration for remote verification
            
        Returns:
            True if validation successful
        """
        try:
            # Get transfer details from DynamoDB
            table = self.dynamodb.Table(self.transfer_table_name)
            response = table.get_item(Key={'transfer_id': transfer_id})
            
            if 'Item' not in response:
                logger.error(f"❌ Transfer {transfer_id} not found in DynamoDB")
                return False
            
            transfer_data = response['Item']
            actual_checksum = transfer_data.get('md5_checksum')
            
            if actual_checksum == expected_checksum:
                logger.info(f"✅ Checksum validation passed: {transfer_id}")
                await self._update_transfer_status(transfer_id, 'validated', {'checksum_match': True})
                return True
            else:
                logger.error(f"❌ Checksum mismatch: {transfer_id}")
                await self._update_transfer_status(transfer_id, 'validation_failed', {
                    'expected': expected_checksum,
                    'actual': actual_checksum
                })
                return False
                
        except Exception as e:
            logger.error(f"❌ Validation error: {str(e)}", exc_info=True)
            return False
    
    async def get_transfer_status(self, execution_arn: str) -> Dict[str, Any]:
        """
        Get Step Functions execution status
        
        Args:
            execution_arn: Step Functions execution ARN
            
        Returns:
            Execution status details
        """
        try:
            response = self.sfn_client.describe_execution(executionArn=execution_arn)
            
            return {
                'status': response['status'],
                'start_date': response['startDate'].isoformat(),
                'stop_date': response.get('stopDate', '').isoformat() if response.get('stopDate') else None,
                'input': json.loads(response['input']),
                'output': json.loads(response.get('output', '{}')),
                'execution_arn': execution_arn
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting execution status: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    async def handle_transfer_failure(
        self,
        transfer_id: str,
        error: str,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Handle transfer failure with retry logic
        
        Args:
            transfer_id: Transfer ID
            error: Error message
            retry_count: Current retry attempt
            
        Returns:
            Retry result
        """
        max_retries = 3
        
        logger.warning(f"⚠️ Transfer failed (attempt {retry_count + 1}/{max_retries}): {transfer_id}")
        
        if retry_count < max_retries:
            # Update status to retrying
            await self._update_transfer_status(transfer_id, 'retrying', {
                'retry_count': retry_count + 1,
                'error': error
            })
            
            return {
                'action': 'retry',
                'retry_count': retry_count + 1,
                'message': 'Transfer will be retried'
            }
        else:
            # Max retries exceeded
            await self._update_transfer_status(transfer_id, 'failed', {
                'retry_count': retry_count,
                'error': error,
                'final_failure': True
            })
            
            return {
                'action': 'failed',
                'retry_count': retry_count,
                'message': 'Max retries exceeded'
            }
    
    def _update_transfer_progress(self, transfer_id: str, bytes_transferred: int, total_bytes: int):
        """Update transfer progress in DynamoDB (synchronous)"""
        try:
            table = self.dynamodb.Table(self.transfer_table_name)
            table.update_item(
                Key={'transfer_id': transfer_id},
                UpdateExpression='SET bytes_transferred = :bytes, progress_percent = :percent, last_updated = :timestamp',
                ExpressionAttributeValues={
                    ':bytes': bytes_transferred,
                    ':percent': round((bytes_transferred / total_bytes) * 100, 2),
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to update progress: {str(e)}")
    
    async def _update_transfer_status(self, transfer_id: str, status: str, metadata: Dict = None):
        """Update transfer status in DynamoDB"""
        try:
            table = self.dynamodb.Table(self.transfer_table_name)
            
            update_expr = 'SET #status = :status, last_updated = :timestamp'
            expr_values = {
                ':status': status,
                ':timestamp': datetime.utcnow().isoformat()
            }
            expr_names = {'#status': 'status'}
            
            if metadata:
                for key, value in metadata.items():
                    update_expr += f', {key} = :{key}'
                    expr_values[f':{key}'] = value
            
            table.update_item(
                Key={'transfer_id': transfer_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values,
                ExpressionAttributeNames=expr_names
            )
            
            logger.info(f"📝 Updated transfer status: {transfer_id} -> {status}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update transfer status: {str(e)}")