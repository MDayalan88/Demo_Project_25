"""
ServiceNow Integration Handler
Creates and manages ServiceNow tickets for audit trail
"""

import aiohttp
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from aws_xray_sdk.core import xray_recorder

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ServiceNowHandler:
    """
    ServiceNow API integration for ticket management
    Creates dual tickets (user + audit) for compliance
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ServiceNow handler
        
        Args:
            config: Configuration containing:
                - servicenow.instance_url: ServiceNow instance URL
                - servicenow.username: API username
                - servicenow.password: API password
                - servicenow.default_assignment_group: Default group
        """
        snow_config = config.get('servicenow', {})
        
        self.instance_url = snow_config.get('instance_url')
        self.username = snow_config.get('username')
        self.password = snow_config.get('password')
        self.default_assignment_group = snow_config.get('default_assignment_group', 'DataOps')
        
        # API endpoints
        self.incident_url = f"{self.instance_url}/api/now/table/incident"
        
        logger.info("✅ ServiceNow Handler initialized")
    
    @xray_recorder.capture('create_dual_tickets')
    async def create_dual_tickets(
        self,
        user_id: str,
        transfer_details: Dict[str, Any],
        assignment_group: str = None
    ) -> Dict[str, Any]:
        """
        Create dual ServiceNow tickets (user + audit)
        
        Args:
            user_id: User requesting transfer
            transfer_details: Transfer details
            assignment_group: Assignment group (default: DataOps)
            
        Returns:
            Dictionary with ticket IDs
        """
        try:
            group = assignment_group or self.default_assignment_group
            
            # Create user ticket
            user_ticket_id = await self._create_ticket(
                short_description=f"File Transfer Request: {transfer_details.get('file_name')}",
                description=self._format_ticket_description(user_id, transfer_details),
                caller_id=user_id,
                assignment_group=group,
                urgency="2",  # Medium
                category="Data Transfer",
                subcategory="S3 to SFTP"
            )
            
            # Create audit ticket
            audit_ticket_id = await self._create_ticket(
                short_description=f"Audit: File Transfer by {user_id}",
                description=self._format_audit_description(user_id, transfer_details),
                caller_id="system",
                assignment_group="Security-Audit",
                urgency="3",  # Low
                category="Audit Trail",
                subcategory="File Transfer",
                state="7"  # Closed (audit only)
            )
            
            logger.info(f"✅ Created ServiceNow tickets: User={user_ticket_id}, Audit={audit_ticket_id}")
            
            return {
                'status': 'success',
                'user_ticket': user_ticket_id,
                'audit_ticket': audit_ticket_id,
                'tickets': [user_ticket_id, audit_ticket_id]
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating ServiceNow tickets: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _create_ticket(
        self,
        short_description: str,
        description: str,
        caller_id: str,
        assignment_group: str,
        urgency: str,
        category: str,
        subcategory: str = None,
        state: str = "2"  # In Progress
    ) -> str:
        """
        Create a single ServiceNow incident ticket
        
        Args:
            short_description: Short summary
            description: Full description
            caller_id: User ID
            assignment_group: Assignment group
            urgency: Urgency level (1=high, 2=medium, 3=low)
            category: Ticket category
            subcategory: Ticket subcategory
            state: Ticket state (2=In Progress, 7=Closed)
            
        Returns:
            Ticket number (e.g., INC0012345)
        """
        payload = {
            "short_description": short_description,
            "description": description,
            "caller_id": caller_id,
            "assignment_group": assignment_group,
            "urgency": urgency,
            "category": category,
            "state": state
        }
        
        if subcategory:
            payload["subcategory"] = subcategory
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.incident_url,
                json=payload,
                auth=aiohttp.BasicAuth(self.username, self.password),
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    ticket_number = result['result']['number']
                    logger.info(f"✅ Created ServiceNow ticket: {ticket_number}")
                    return ticket_number
                else:
                    error_text = await response.text()
                    logger.error(f"❌ ServiceNow API error ({response.status}): {error_text}")
                    raise Exception(f"ServiceNow API error: {response.status}")
    
    @xray_recorder.capture('update_ticket_status')
    async def update_ticket_status(
        self,
        ticket_number: str,
        state: str,
        work_notes: str = None
    ) -> Dict[str, Any]:
        """
        Update ticket status
        
        Args:
            ticket_number: Ticket number (e.g., INC0012345)
            state: New state (2=In Progress, 6=Resolved, 7=Closed)
            work_notes: Optional work notes
            
        Returns:
            Update result
        """
        try:
            # Get ticket sys_id
            sys_id = await self._get_ticket_sys_id(ticket_number)
            
            if not sys_id:
                return {
                    'status': 'error',
                    'error': f"Ticket {ticket_number} not found"
                }
            
            # Update ticket
            payload = {"state": state}
            if work_notes:
                payload["work_notes"] = work_notes
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.incident_url}/{sys_id}",
                    json=payload,
                    auth=aiohttp.BasicAuth(self.username, self.password),
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ Updated ticket {ticket_number} to state {state}")
                        return {'status': 'success', 'ticket_number': ticket_number}
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Error updating ticket: {error_text}")
                        return {'status': 'error', 'error': error_text}
                        
        except Exception as e:
            logger.error(f"❌ Error updating ticket status: {str(e)}", exc_info=True)
            return {'status': 'error', 'error': str(e)}
    
    async def _get_ticket_sys_id(self, ticket_number: str) -> Optional[str]:
        """Get ServiceNow sys_id for a ticket number"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.incident_url,
                    params={'sysparm_query': f'number={ticket_number}'},
                    auth=aiohttp.BasicAuth(self.username, self.password)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result['result']:
                            return result['result'][0]['sys_id']
            return None
        except Exception as e:
            logger.error(f"Error getting ticket sys_id: {str(e)}")
            return None
    
    def _format_ticket_description(self, user_id: str, details: Dict) -> str:
        """Format ticket description"""
        return f"""
File Transfer Request

User: {user_id}
File: {details.get('file_name', 'N/A')}
Bucket: {details.get('bucket_name', 'N/A')}
Region: {details.get('region', 'N/A')}
Destination: {details.get('destination_type', 'SFTP')}
Size: {details.get('file_size_mb', 'N/A')} MB

Requested: {datetime.utcnow().isoformat()}

This transfer is managed by FileFerry AI Agent.
"""
    
    def _format_audit_description(self, user_id: str, details: Dict) -> str:
        """Format audit ticket description"""
        return f"""
AUDIT TRAIL: File Transfer Activity

User: {user_id}
Action: File Transfer
File: {details.get('file_name', 'N/A')}
Source: s3://{details.get('bucket_name', 'N/A')}/{details.get('file_key', 'N/A')}
Destination: {details.get('destination_type', 'SFTP')}
Timestamp: {datetime.utcnow().isoformat()}

Security Notes:
- SSO authentication enforced
- Read-only S3 access
- 10-second auto-logout policy
- Full audit trail maintained

Managed by: FileFerry AI Agent
"""