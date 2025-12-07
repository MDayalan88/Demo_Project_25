"""
Lambda Function: Authenticate SSO
Authenticates user and creates 10-second SSO session
"""

import json
import boto3
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any


dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'FileFerry-ActiveSessions'


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Authenticate user and create SSO session
    
    Event structure:
    {
        "user_id": "user@example.com",
        "servicenow_tickets": ["INC0010001", "INC0010002"]
    }
    """
    
    try:
        user_id = event['user_id']
        servicenow_request_id = event['servicenow_tickets'][0]  # User ticket
        
        print(f"🔐 Authenticating user: {user_id}")
        
        # Generate session token
        session_token = str(uuid.uuid4())
        
        # Calculate TTL (10 seconds from now)
        ttl = int((datetime.utcnow() + timedelta(seconds=10)).timestamp())
        
        # Store session in DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(
            Item={
                'session_token': session_token,
                'user_id': user_id,
                'servicenow_request_id': servicenow_request_id,
                'region': 'us-east-1',
                'created_at': datetime.utcnow().isoformat(),
                'ttl': ttl
            }
        )
        
        print(f"✅ SSO session created: {session_token[:8]}... (expires in 10s)")
        
        return {
            'status': 'authenticated',
            'session_token': session_token,
            'user_id': user_id,
            'session_duration': 10,
            'expires_at': ttl
        }
        
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }
