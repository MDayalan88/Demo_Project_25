"""
Lambda Function: Validate Input
Validates transfer request parameters before processing
"""

import json
import boto3
from typing import Dict, Any


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Validate transfer request input
    
    Event structure:
    {
        "user_id": "user@example.com",
        "transfer_plan": {
            "source_bucket": "my-bucket",
            "source_key": "file.txt",
            "destination_host": "ftp.example.com",
            "destination_port": 21,
            "transfer_type": "ftp"
        },
        "servicenow_tickets": ["INC0010001", "INC0010002"]
    }
    """
    
    try:
        print(f"📥 Validating input: {json.dumps(event)}")
        
        # Required fields
        required_fields = ['user_id', 'transfer_plan', 'servicenow_tickets']
        missing_fields = [field for field in required_fields if field not in event]
        
        if missing_fields:
            return {
                'status': 'invalid',
                'error': f"Missing required fields: {', '.join(missing_fields)}",
                'valid': False
            }
        
        # Validate transfer_plan
        transfer_plan = event['transfer_plan']
        required_plan_fields = ['source_bucket', 'source_key', 'destination_host']
        missing_plan_fields = [field for field in required_plan_fields if field not in transfer_plan]
        
        if missing_plan_fields:
            return {
                'status': 'invalid',
                'error': f"Missing transfer plan fields: {', '.join(missing_plan_fields)}",
                'valid': False
            }
        
        # Validate S3 bucket exists
        s3_client = boto3.client('s3')
        
        try:
            s3_client.head_bucket(Bucket=transfer_plan['source_bucket'])
        except Exception as e:
            return {
                'status': 'invalid',
                'error': f"S3 bucket not accessible: {str(e)}",
                'valid': False
            }
        
        # Validate S3 object exists
        try:
            s3_client.head_object(
                Bucket=transfer_plan['source_bucket'],
                Key=transfer_plan['source_key']
            )
        except Exception as e:
            return {
                'status': 'invalid',
                'error': f"S3 object not found: {str(e)}",
                'valid': False
            }
        
        # Validate ServiceNow tickets
        if not isinstance(event['servicenow_tickets'], list) or len(event['servicenow_tickets']) < 2:
            return {
                'status': 'invalid',
                'error': 'Expected 2 ServiceNow tickets (user + audit)',
                'valid': False
            }
        
        print("✅ Input validation passed")
        
        return {
            'status': 'valid',
            'valid': True,
            'message': 'All validation checks passed'
        }
        
    except Exception as e:
        print(f"❌ Validation error: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'valid': False
        }
