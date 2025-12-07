import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from ..models.transfer_job import TransferJob
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TransferService:
    """
    Enhanced transfer service with AI-driven optimization and intelligence
    """
    
    def __init__(self, transfer_handler, notification_service, monitoring_service):
        self.transfer_handler = transfer_handler
        self.notification_service = notification_service
        self.monitoring_service = monitoring_service

    def start_transfer(self, source, destination):
        """Legacy synchronous transfer method"""
        transfer_job = self.create_transfer_job(source, destination)
        self.monitoring_service.track_job_start(transfer_job)
        try:
            self.transfer_handler.initiate_transfer(transfer_job)
            self.notification_service.send_notification(transfer_job, "Transfer started.")
        except Exception as e:
            self.notification_service.send_notification(transfer_job, f"Transfer failed: {str(e)}")
            self.monitoring_service.track_job_failure(transfer_job, str(e))
        else:
            self.monitoring_service.track_job_completion(transfer_job)
            self.notification_service.send_notification(transfer_job, "Transfer completed successfully.")
    
    async def start_transfer_async(self, transfer_job: TransferJob, s3_handler) -> None:
        """
        Start asynchronous file transfer with AI-driven optimization
        
        Args:
            transfer_job: Transfer job details
            s3_handler: S3 handler for source operations
        """
        logger.info(f"Starting async transfer for job: {transfer_job.job_id}")
        
        await self.monitoring_service.track_job_start(transfer_job)
        transfer_job.status = 'in_progress'
        transfer_job.start_time = datetime.utcnow()
        
        try:
            # AI-driven transfer optimization
            optimization = await self._optimize_transfer(transfer_job)
            logger.info(f"Transfer optimization: {optimization}")
            
            # Get file from S3 (streaming for large files)
            file_stream = await s3_handler.get_file_stream(
                transfer_job.source_bucket,
                transfer_job.source_key,
                transfer_job.source_region
            )
            
            # Initiate transfer to destination
            if transfer_job.destination_type == 'sftp':
                await self.transfer_handler.upload_file_async(
                    file_stream,
                    transfer_job.source_key,
                    optimization
                )
            elif transfer_job.destination_type == 'ftp':
                await self.transfer_handler.upload_file_async(
                    file_stream,
                    transfer_job.source_key,
                    optimization
                )
            
            # Success
            transfer_job.status = 'completed'
            transfer_job.end_time = datetime.utcnow()
            transfer_job.duration = (transfer_job.end_time - transfer_job.start_time).total_seconds()
            
            await self.monitoring_service.track_job_completion(transfer_job)
            await self.notification_service.send_notification(
                transfer_job, 
                "Transfer completed successfully."
            )
            
            logger.info(f"Transfer completed: {transfer_job.job_id} in {transfer_job.duration}s")
            
        except Exception as e:
            transfer_job.status = 'failed'
            transfer_job.error_message = str(e)
            transfer_job.end_time = datetime.utcnow()
            
            logger.error(f"Transfer failed: {transfer_job.job_id} - {str(e)}", exc_info=True)
            
            await self.notification_service.send_notification(
                transfer_job, 
                f"Transfer failed: {str(e)}"
            )
            await self.monitoring_service.track_job_failure(transfer_job, str(e))
    
    async def _optimize_transfer(self, transfer_job: TransferJob) -> Dict[str, Any]:
        """
        AI-driven transfer optimization based on file characteristics
        
        Args:
            transfer_job: Transfer job to optimize
            
        Returns:
            Optimization parameters
        """
        file_size = transfer_job.file_size
        
        optimization = {
            'chunk_size': 8 * 1024 * 1024,  # 8 MB default
            'compression': False,
            'parallel_streams': 1,
            'retry_strategy': 'exponential_backoff',
            'max_retries': 3
        }
        
        # Large files (> 100 MB)
        if file_size > 100 * 1024 * 1024:
            optimization['chunk_size'] = 32 * 1024 * 1024  # 32 MB chunks
            optimization['compression'] = True
            logger.info(f"Large file detected ({file_size} bytes), enabling compression")
        
        # Very large files (> 1 GB)
        if file_size > 1024 * 1024 * 1024:
            optimization['parallel_streams'] = 3
            optimization['chunk_size'] = 64 * 1024 * 1024  # 64 MB chunks
            logger.info(f"Very large file detected, enabling parallel streams")
        
        # Adjust based on destination type
        if transfer_job.destination_type == 'ftp':
            # FTP is less reliable, increase retries
            optimization['max_retries'] = 5
        
        return optimization

    def create_transfer_job(self, source, destination):
        """Legacy method to create transfer job"""
        # Logic to create and return a transfer job object
        pass

    def monitor_transfer(self, transfer_job):
        """Monitor the status of the transfer job"""
        # Logic to monitor the status of the transfer job
        pass
    
    async def estimate_transfer_time(self, file_size: int, destination_type: str) -> Dict[str, Any]:
        """
        AI-driven estimation of transfer time
        
        Args:
            file_size: File size in bytes
            destination_type: 'sftp' or 'ftp'
            
        Returns:
            Estimation details
        """
        # Baseline speeds (MB/s)
        speeds = {
            'sftp': 15,  # 15 MB/s average
            'ftp': 10    # 10 MB/s average
        }
        
        base_speed = speeds.get(destination_type, 10)
        
        # Adjust for file size (larger files transfer more efficiently)
        if file_size > 1024 * 1024 * 1024:  # > 1 GB
            speed = base_speed * 1.2
        else:
            speed = base_speed * 0.8
        
        # Calculate time
        time_seconds = file_size / (speed * 1024 * 1024)
        
        # Add overhead (15%)
        time_seconds *= 1.15
        
        return {
            'estimated_seconds': int(time_seconds),
            'estimated_minutes': round(time_seconds / 60, 1),
            'estimated_speed_mbps': round(speed, 1),
            'confidence': 'medium'
        }