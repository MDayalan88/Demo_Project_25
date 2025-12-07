"""
Datadog Monitoring Service
Provides real-time monitoring and metrics tracking
"""

from datadog import initialize, statsd, api
from typing import Dict, Any, Optional
from datetime import datetime
from ..models.transfer_job import TransferJob
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MonitoringService:
    """
    Enhanced monitoring service with Datadog integration
    Tracks metrics, logs, and performance data
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize monitoring service with Datadog
        
        Args:
            config: Configuration containing:
                - datadog_api_key: Datadog API key
                - datadog_app_key: Datadog application key
                - environment: Environment name (dev/staging/prod)
                - service_name: Service name for tagging
        """
        self.logger = logger
        self.metrics = {}
        self.enabled = config.get('enabled', True)
        self.environment = config.get('environment', 'production')
        self.service_name = config.get('service_name', 'fileferry-agent')
        
        # Initialize Datadog
        if self.enabled and config.get('datadog_api_key'):
            try:
                initialize(
                    api_key=config.get('datadog_api_key'),
                    app_key=config.get('datadog_app_key'),
                    statsd_host=config.get('statsd_host', 'localhost'),
                    statsd_port=config.get('statsd_port', 8125)
                )
                logger.info("Datadog monitoring initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Datadog: {str(e)}")
                self.enabled = False
        else:
            logger.warning("Datadog monitoring not configured")
    
    async def track_job_start(self, transfer_job: TransferJob) -> None:
        """Track when a transfer job starts"""
        self.metrics[transfer_job.job_id] = {
            'status': 'started',
            'start_time': datetime.utcnow(),
            'file_size': transfer_job.file_size
        }
        
        await self.track_metric('transfer.started', 1, {
            'job_id': transfer_job.job_id,
            'destination_type': transfer_job.destination_type,
            'environment': self.environment
        })
        
        logger.info(f"Tracking started: {transfer_job.job_id}")
    
    async def track_job_completion(self, transfer_job: TransferJob) -> None:
        """Track when a transfer job completes successfully"""
        if transfer_job.job_id in self.metrics:
            self.metrics[transfer_job.job_id]['status'] = 'completed'
            self.metrics[transfer_job.job_id]['end_time'] = datetime.utcnow()
            self.metrics[transfer_job.job_id]['duration'] = transfer_job.duration
        
        await self.track_metric('transfer.completed', 1, {
            'job_id': transfer_job.job_id,
            'destination_type': transfer_job.destination_type,
            'duration': transfer_job.duration,
            'file_size': transfer_job.file_size
        })
        
        # Track transfer duration histogram
        if self.enabled:
            statsd.histogram(
                'fileferry.transfer.duration',
                transfer_job.duration,
                tags=[
                    f'environment:{self.environment}',
                    f'destination:{transfer_job.destination_type}',
                    f'service:{self.service_name}'
                ]
            )
        
        logger.info(f"Tracking completed: {transfer_job.job_id} in {transfer_job.duration}s")
    
    async def track_job_failure(self, transfer_job: TransferJob, error_message: str) -> None:
        """Track when a transfer job fails"""
        if transfer_job.job_id in self.metrics:
            self.metrics[transfer_job.job_id]['status'] = 'failed'
            self.metrics[transfer_job.job_id]['error'] = error_message
        
        await self.track_metric('transfer.failed', 1, {
            'job_id': transfer_job.job_id,
            'destination_type': transfer_job.destination_type,
            'error': error_message[:100]  # Truncate long errors
        })
        
        logger.error(f"Tracking failed: {transfer_job.job_id} - {error_message}")
    
    async def track_metric(
        self, 
        metric_name: str, 
        value: float, 
        tags: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track a custom metric in Datadog
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for the metric
        """
        if not self.enabled:
            logger.debug(f"Metric (disabled): {metric_name} = {value}")
            return
        
        try:
            # Convert tags dict to Datadog format
            tag_list = [f"{k}:{v}" for k, v in (tags or {}).items()]
            tag_list.extend([
                f'environment:{self.environment}',
                f'service:{self.service_name}'
            ])
            
            # Send metric
            statsd.increment(
                f'fileferry.{metric_name}',
                value=int(value),
                tags=tag_list
            )
            
            logger.debug(f"Metric tracked: {metric_name} = {value}")
            
        except Exception as e:
            logger.error(f"Failed to track metric {metric_name}: {str(e)}")
    
    async def track_transfer_progress(self, transfer_job: TransferJob) -> None:
        """
        Track transfer progress for real-time monitoring
        
        Args:
            transfer_job: Transfer job to track
        """
        if not self.enabled:
            return
        
        try:
            # Calculate progress percentage
            progress = transfer_job.progress if hasattr(transfer_job, 'progress') else 0
            
            statsd.gauge(
                'fileferry.transfer.progress',
                progress,
                tags=[
                    f'job_id:{transfer_job.job_id}',
                    f'environment:{self.environment}',
                    f'destination:{transfer_job.destination_type}'
                ]
            )
            
            logger.debug(f"Progress tracked: {transfer_job.job_id} - {progress}%")
            
        except Exception as e:
            logger.error(f"Failed to track progress: {str(e)}")
    
    async def track_error(self, error_type: str, error_message: str) -> None:
        """
        Track errors in Datadog
        
        Args:
            error_type: Type/category of error
            error_message: Error message
        """
        await self.track_metric('error', 1, {
            'error_type': error_type,
            'message': error_message[:100]
        })

    def track_transfer(self, transfer_id, status, duration):
        """Legacy method for backward compatibility"""
        self.metrics[transfer_id] = {
            'status': status,
            'duration': duration
        }
        self.logger.info(f"Transfer {transfer_id}: Status - {status}, Duration - {duration} seconds")

    def get_metrics(self):
        """Get all tracked metrics"""
        return self.metrics

    def log_performance(self):
        """Log performance metrics"""
        for transfer_id, data in self.metrics.items():
            self.logger.info(f"Transfer ID: {transfer_id}, Status: {data['status']}, Duration: {data.get('duration', 'N/A')} seconds")
    
    async def create_dashboard_event(
        self, 
        title: str, 
        text: str, 
        alert_type: str = 'info'
    ) -> None:
        """
        Create an event in Datadog for dashboards
        
        Args:
            title: Event title
            text: Event description
            alert_type: 'info', 'success', 'warning', or 'error'
        """
        if not self.enabled:
            return
        
        try:
            api.Event.create(
                title=title,
                text=text,
                tags=[
                    f'environment:{self.environment}',
                    f'service:{self.service_name}'
                ],
                alert_type=alert_type
            )
            
            logger.info(f"Datadog event created: {title}")
            
        except Exception as e:
            logger.error(f"Failed to create Datadog event: {str(e)}")