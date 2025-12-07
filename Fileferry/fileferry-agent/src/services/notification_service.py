import aiohttp
import json
from typing import Dict, Any, Optional
from datetime import datetime
from ..models.transfer_job import TransferJob
from ..utils.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """
    Enhanced notification service with Microsoft Teams integration
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize notification service
        
        Args:
            config: Configuration containing:
                - teams_webhook_url: Microsoft Teams incoming webhook URL
                - email_enabled: Enable email notifications
                - slack_webhook_url: Optional Slack webhook
        """
        self.config = config
        self.teams_webhook_url = config.get('teams_webhook_url')
        self.email_enabled = config.get('email_enabled', False)
        self.slack_webhook_url = config.get('slack_webhook_url')
        self.enabled = config.get('enabled', True)
        
        logger.info("Notification service initialized")

    def send_notification(self, message, channel=None):
        """Legacy synchronous notification method"""
        if channel == 'email':
            self.send_email_notification_sync(message)
        elif channel == 'slack':
            self.send_slack_notification_sync(message)
        elif channel == 'teams':
            self.send_teams_notification_sync(message)
        else:
            logger.info(f"Notification: {message}")
    
    async def send_teams_notification(
        self, 
        message: str, 
        transfer_job: Optional[TransferJob] = None,
        notification_type: str = 'info'
    ) -> bool:
        """
        Send notification to Microsoft Teams channel
        
        Args:
            message: Notification message
            transfer_job: Optional transfer job for additional context
            notification_type: 'success', 'error', 'warning', or 'info'
            
        Returns:
            True if successful
        """
        if not self.enabled or not self.teams_webhook_url:
            logger.warning("Teams notifications not configured")
            return False
        
        try:
            # Build adaptive card for rich formatting
            card = self._build_teams_card(message, transfer_job, notification_type)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.teams_webhook_url,
                    json=card,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        logger.info("Teams notification sent successfully")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send Teams notification: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending Teams notification: {str(e)}", exc_info=True)
            return False
    
    def _build_teams_card(
        self, 
        message: str, 
        transfer_job: Optional[TransferJob],
        notification_type: str
    ) -> Dict[str, Any]:
        """
        Build Microsoft Teams adaptive card
        
        Args:
            message: Main message
            transfer_job: Transfer job details
            notification_type: Notification type
            
        Returns:
            Adaptive card JSON
        """
        # Color scheme based on type
        theme_color = {
            'success': '00C851',  # Green
            'error': 'FF4444',    # Red
            'warning': 'FFBB33',  # Orange
            'info': '33B5E5'      # Blue
        }
        
        # Build facts for additional details
        facts = []
        if transfer_job:
            facts.extend([
                {"name": "File", "value": transfer_job.source_key},
                {"name": "Source", "value": f"{transfer_job.source_bucket} ({transfer_job.source_region})"},
                {"name": "Destination", "value": f"{transfer_job.destination_type.upper()} Server"},
                {"name": "Job ID", "value": transfer_job.job_id},
            ])
            
            if transfer_job.file_size:
                facts.append({
                    "name": "Size", 
                    "value": self._format_size(transfer_job.file_size)
                })
            
            if transfer_job.duration:
                facts.append({
                    "name": "Duration", 
                    "value": f"{transfer_job.duration:.1f} seconds"
                })
            
            if transfer_job.user_ticket:
                facts.append({
                    "name": "User Ticket", 
                    "value": transfer_job.user_ticket
                })
        
        # Build card
        card = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": "FileFerry Transfer Notification",
            "themeColor": theme_color.get(notification_type, '33B5E5'),
            "title": "FileFerry Agent - File Transfer Update",
            "sections": [
                {
                    "activityTitle": message,
                    "activitySubtitle": f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    "facts": facts,
                    "markdown": True
                }
            ]
        }
        
        return card

    def send_email_notification_sync(self, message):
        """Legacy email notification"""
        # Logic to send email notification
        logger.info(f"Email notification: {message}")

    def send_slack_notification_sync(self, message):
        """Legacy Slack notification"""
        # Logic to send Slack notification
        logger.info(f"Slack notification: {message}")

    def send_teams_notification_sync(self, message):
        """Legacy Teams notification"""
        # Logic to send Microsoft Teams notification
        logger.info(f"Teams notification: {message}")
    
    async def send_slack_notification(
        self,
        message: str,
        transfer_job: Optional[TransferJob] = None
    ) -> bool:
        """
        Send notification to Slack (if configured)
        
        Args:
            message: Notification message
            transfer_job: Optional transfer job
            
        Returns:
            True if successful
        """
        if not self.slack_webhook_url:
            return False
        
        try:
            payload = {
                "text": message,
                "username": "FileFerry Agent",
                "icon_emoji": ":ferry:"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.slack_webhook_url,
                    json=payload
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
            return False

    def log_notification(self, message, channel):
        """Log the notification"""
        logger.info(f"Notification sent to {channel}: {message}")
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"