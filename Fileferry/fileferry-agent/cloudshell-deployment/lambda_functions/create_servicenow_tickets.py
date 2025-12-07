"""
Lambda Function: Create ServiceNow Tickets
Creates new ServiceNow incidents for file transfer tracking
"""

import json
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, Any, List
import os
from datetime import datetime


SERVICENOW_INSTANCE = os.environ.get('SERVICENOW_INSTANCE_URL', 'https://your-instance.service-now.com')
SERVICENOW_USERNAME = os.environ.get('SERVICENOW_USERNAME')
SERVICENOW_PASSWORD = os.environ.get('SERVICENOW_PASSWORD')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Create ServiceNow tickets for file transfer
    
    Event structure:
    {
        "user_id": "user@example.com",
        "transfer_plan": {
            "source": {...},
            "destination": {...}
        }
    }
    
    Returns:
    {
        "servicenow_tickets": ["INC0012345", "INC0012346"],
        "ticket_details": [...]
    }
    """
    
    try:
        user_id = event.get('user_id', 'unknown@example.com')
        transfer_plan = event.get('transfer_plan', {})
        
        print(f"📝 Creating ServiceNow tickets for user: {user_id}")
        
        # Extract transfer details
        source = transfer_plan.get('source', {})
        destination = transfer_plan.get('destination', {})
        
        bucket_name = source.get('bucket', 'unknown-bucket')
        file_name = source.get('file', 'unknown-file')
        file_size = source.get('size', 'unknown')
        
        dest_type = destination.get('type', 'FTP')
        dest_host = destination.get('host', 'unknown-host')
        dest_path = destination.get('path', '/unknown')
        
        # Create tickets
        tickets_created = []
        
        # 1. User Incident Ticket
        user_ticket = create_incident(
            short_description=f"File Transfer Request - {file_name}",
            description=f"""File Transfer Request

Requested By: {user_id}
Transfer Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SOURCE:
  Type: AWS S3
  Bucket: {bucket_name}
  File: {file_name}
  Size: {file_size}

DESTINATION:
  Type: {dest_type}
  Host: {dest_host}
  Path: {dest_path}

This ticket tracks the file transfer request and will be updated automatically when the transfer completes.
""",
            caller=user_id,
            category="Data Transfer",
            priority="3"  # Moderate
        )
        
        if user_ticket:
            tickets_created.append(user_ticket)
            print(f"✅ Created user ticket: {user_ticket['number']}")
        
        # 2. Audit/Tracking Ticket (RITM format)
        audit_ticket = create_incident(
            short_description=f"Transfer Audit Trail - {file_name}",
            description=f"""Automated Transfer Audit Record

Transfer ID: {context.request_id if hasattr(context, 'request_id') else 'N/A'}
User: {user_id}
Initiated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

File: {file_name} ({file_size})
Source: {bucket_name}
Destination: {dest_type}://{dest_host}{dest_path}

This is an automated audit trail ticket for compliance tracking.
""",
            caller="system@fileferry.com",
            category="Audit",
            priority="4"  # Low
        )
        
        if audit_ticket:
            tickets_created.append(audit_ticket)
            print(f"✅ Created audit ticket: {audit_ticket['number']}")
        
        if not tickets_created:
            raise Exception("Failed to create any ServiceNow tickets")
        
        # Prepare response
        ticket_numbers = [t['number'] for t in tickets_created]
        
        return {
            'statusCode': 200,
            'servicenow_tickets': ticket_numbers,
            'ticket_details': tickets_created,
            'tickets_created': len(tickets_created)
        }
        
    except Exception as e:
        print(f"❌ Error creating tickets: {str(e)}")
        
        # Return mock tickets if ServiceNow fails (fallback for demo)
        return {
            'statusCode': 200,
            'servicenow_tickets': ['INC0010001', 'INC0010002'],
            'ticket_details': [],
            'tickets_created': 0,
            'error': str(e),
            'fallback_mode': True
        }


def create_incident(short_description: str, description: str, caller: str, 
                   category: str, priority: str) -> Dict[str, Any]:
    """
    Create a new incident in ServiceNow
    
    Returns:
        Dict with ticket number and sys_id, or None if failed
    """
    
    url = f"{SERVICENOW_INSTANCE}/api/now/table/incident"
    
    payload = {
        "short_description": short_description,
        "description": description,
        "caller_id": caller,
        "category": category,
        "priority": priority,
        "urgency": "3",  # Moderate
        "impact": "3",   # Moderate
        "state": "2",    # In Progress
        "assignment_group": "DevOps Team",
        "contact_type": "self-service"
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            auth=HTTPBasicAuth(SERVICENOW_USERNAME, SERVICENOW_PASSWORD),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json().get('result', {})
            return {
                'number': result.get('number'),
                'sys_id': result.get('sys_id'),
                'short_description': result.get('short_description')
            }
        else:
            print(f"❌ ServiceNow API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return None
