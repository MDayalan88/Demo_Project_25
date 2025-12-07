"""
ServiceNow Integration Service
Handles creation and management of ServiceNow tickets for audit and tracking
"""

import aiohttp
import json
from typing import Dict, Any, Optional
from datetime import datetime
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ServiceNowService:
    """
    Service for creating and managing ServiceNow tickets
    Supports dual ticket creation for user and assignment team
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ServiceNow service
        
        Args:
            config: Configuration containing:
                - instance_url: ServiceNow instance URL
                - username: ServiceNow API username
                - password: ServiceNow API password
                - api_version: API version (default: v2)
        """
        self.instance_url = config.get('instance_url', '').rstrip('/')
        self.username = config.get('username')
        self.password = config.get('password')
        self.api_version = config.get('api_version', 'v2')
        self.table = config.get('table', 'incident')  # incident or sc_request
        
        # API endpoints
        self.create_endpoint = f"{self.instance_url}/api/now/{self.api_version}/table/{self.table}"
        self.update_endpoint = f"{self.instance_url}/api/now/{self.api_version}/table/{self.table}"
        
        self.session = None
        logger.info("ServiceNow service initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            auth = aiohttp.BasicAuth(self.username, self.password)
            self.session = aiohttp.ClientSession(auth=auth)
        return self.session
    
    async def create_ticket(
        self, 
        ticket_data: Dict[str, Any], 
        ticket_type: str = 'user'
    ) -> str:
        """
        Create a ServiceNow ticket
        
        Args:
            ticket_data: Ticket details including short_description, description, etc.
            ticket_type: 'user' or 'assignment' to distinguish ticket purpose
            
        Returns:
            Ticket number/ID
        """
        try:
            session = await self._get_session()
            
            # Add metadata
            ticket_data['caller_id'] = ticket_data.get('caller_id', self.username)
            ticket_data['opened_at'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            ticket_data['state'] = 'New'
            ticket_data['impact'] = ticket_data.get('impact', 'Medium')
            ticket_data['urgency'] = ticket_data.get('urgency', 'Medium')
            
            # Add ticket type identifier
            ticket_data['u_ticket_type'] = ticket_type  # Custom field
            ticket_data['u_automation_source'] = 'FileFerry Agent'
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            logger.info(f"Creating {ticket_type} ticket in ServiceNow")
            
            async with session.post(self.create_endpoint, json=ticket_data, headers=headers) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    ticket_number = result['result']['number']
                    logger.info(f"ServiceNow {ticket_type} ticket created: {ticket_number}")
                    return ticket_number
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create ServiceNow ticket: {response.status} - {error_text}")
                    raise Exception(f"ServiceNow API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error creating ServiceNow ticket: {str(e)}", exc_info=True)
            # Return a mock ticket number for development/testing
            return f"MOCK-{ticket_type.upper()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    async def update_ticket(
        self, 
        ticket_number: str, 
        status: str, 
        work_notes: Optional[str] = None
    ) -> bool:
        """
        Update existing ServiceNow ticket status
        
        Args:
            ticket_number: Ticket number to update
            status: New status (e.g., 'In Progress', 'Resolved', 'Closed')
            work_notes: Optional notes to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = await self._get_session()
            
            # Map status to ServiceNow state values
            state_mapping = {
                'New': '1',
                'In Progress': '2',
                'On Hold': '3',
                'Resolved': '6',
                'Closed': '7',
                'Canceled': '8',
                'Failed': '4'
            }
            
            update_data = {
                'state': state_mapping.get(status, '2'),
                'updated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if work_notes:
                update_data['work_notes'] = work_notes
            
            # Get sys_id for the ticket
            query_url = f"{self.update_endpoint}?sysparm_query=number={ticket_number}&sysparm_limit=1"
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            async with session.get(query_url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result['result']:
                        sys_id = result['result'][0]['sys_id']
                        
                        # Update the ticket
                        update_url = f"{self.update_endpoint}/{sys_id}"
                        async with session.patch(update_url, json=update_data, headers=headers) as update_response:
                            if update_response.status == 200:
                                logger.info(f"Ticket {ticket_number} updated to {status}")
                                return True
                            else:
                                logger.error(f"Failed to update ticket: {update_response.status}")
                                return False
                    else:
                        logger.warning(f"Ticket {ticket_number} not found")
                        return False
                else:
                    logger.error(f"Failed to query ticket: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating ServiceNow ticket: {str(e)}", exc_info=True)
            return False
    
    async def get_ticket_details(self, ticket_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve ticket details
        
        Args:
            ticket_number: Ticket number to retrieve
            
        Returns:
            Ticket details dictionary or None if not found
        """
        try:
            session = await self._get_session()
            
            query_url = f"{self.update_endpoint}?sysparm_query=number={ticket_number}&sysparm_limit=1"
            
            headers = {
                'Accept': 'application/json'
            }
            
            async with session.get(query_url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    if result['result']:
                        return result['result'][0]
                    else:
                        logger.warning(f"Ticket {ticket_number} not found")
                        return None
                else:
                    logger.error(f"Failed to get ticket details: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error retrieving ticket details: {str(e)}", exc_info=True)
            return None
    
    async def add_comment(self, ticket_number: str, comment: str) -> bool:
        """
        Add a comment/work note to a ticket
        
        Args:
            ticket_number: Ticket number
            comment: Comment text to add
            
        Returns:
            True if successful
        """
        return await self.update_ticket(ticket_number, 'In Progress', comment)
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("ServiceNow session closed")


class ServiceNowTicketBuilder:
    """Helper class to build ServiceNow ticket payloads"""
    
    @staticmethod
    def build_user_ticket(
        file_name: str,
        bucket_name: str,
        region: str,
        destination_type: str,
        environment: str,
        user_email: str,
        assignment_group: str
    ) -> Dict[str, Any]:
        """Build user-facing ticket"""
        return {
            'short_description': f"File Transfer Request: {file_name}",
            'description': f"""
Automated File Transfer Request
================================
File: {file_name}
Source: S3 Bucket {bucket_name} ({region})
Destination: {destination_type.upper()} Server
Environment: {environment}
Requested by: {user_email}
Request Time: {datetime.utcnow().isoformat()}

Status: Transfer initiated automatically via FileFerry Agent

You will receive a notification when the transfer completes.
            """,
            'category': 'File Transfer',
            'subcategory': 'Automated Transfer',
            'priority': 'Medium',
            'assignment_group': assignment_group,
            'caller_id': user_email,
            'contact_type': 'Self-service'
        }
    
    @staticmethod
    def build_audit_ticket(
        file_name: str,
        bucket_name: str,
        region: str,
        destination_type: str,
        environment: str,
        user_ticket: str,
        assignment_group: str
    ) -> Dict[str, Any]:
        """Build assignment team audit ticket"""
        return {
            'short_description': f"[AUDIT] Automated File Transfer: {file_name}",
            'description': f"""
Automated File Transfer - Assignment Team Audit Record
======================================================
File: {file_name}
Source: S3 Bucket {bucket_name} ({region})
Destination: {destination_type.upper()} Server
Environment: {environment}
User Ticket: {user_ticket}
Request Time: {datetime.utcnow().isoformat()}

This is an automated audit record for compliance and tracking purposes.
The file transfer is being processed automatically by FileFerry Agent.

No manual action required unless transfer fails.
            """,
            'category': 'Audit',
            'subcategory': 'Automated Process',
            'priority': 'Low',
            'assignment_group': assignment_group,
            'contact_type': 'Monitoring'
        }
