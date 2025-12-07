"""
Lambda Function: Notify User
Sends notification to user via Teams/Slack and updates DynamoDB
"""

import json
import boto3
import requests
from typing import Dict, Any
from datetime import datetime


dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Notify user of transfer completion
    
    Event structure:
    {
        "user_id": "user@example.com",
        "transfer_result": {
            "status": "completed",
            "bytes_transferred": 1024
        },
        "servicenow_tickets": ["INC0010001"]
    }
    """
    
    try:
        user_id = event['user_id']
        transfer_result = event.get('transfer_result', {})
        tickets = event.get('servicenow_tickets', [])
        
        print(f"📢 Notifying user: {user_id}")
        
        # Update DynamoDB TransferRequests table
        transfer_id = event.get('transfer_id', f"transfer-{int(datetime.utcnow().timestamp())}")
        
        table = dynamodb.Table('FileFerry-TransferRequests')
        table.put_item(
            Item={
                'transfer_id': transfer_id,
                'user_id': user_id,
                'status': transfer_result.get('status', 'completed'),
                'bytes_transferred': transfer_result.get('bytes_transferred', 0),
                'servicenow_tickets': tickets,
                'completed_at': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }
        )
        
        print(f"✅ DynamoDB updated: {transfer_id}")
        
        # Send CloudWatch metric
        cloudwatch.put_metric_data(
            Namespace='FileFerry',
            MetricData=[
                {
                    'MetricName': 'TransferCompleted',
                    'Value': 1,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': [
                        {'Name': 'Status', 'Value': transfer_result.get('status', 'completed')}
                    ]
                },
                {
                    'MetricName': 'BytesTransferred',
                    'Value': transfer_result.get('bytes_transferred', 0),
                    'Unit': 'Bytes',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
        
        print("✅ CloudWatch metrics sent")
        
        # Send Teams notification (placeholder - requires webhook URL)
        teams_webhook = event.get('teams_webhook_url')
        
        if teams_webhook:
            notification = create_teams_notification(
                user_id,
                transfer_result,
                tickets
            )
            
            response = requests.post(teams_webhook, json=notification)
            
            if response.status_code == 200:
                print("✅ Teams notification sent")
            else:
                print(f"⚠️ Teams notification failed: {response.status_code}")
        
        return {
            'status': 'notified',
            'user_id': user_id,
            'transfer_id': transfer_id,
            'notification_sent': teams_webhook is not None
        }
        
    except Exception as e:
        print(f"❌ Notification error: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


def create_teams_notification(user_id: str, result: Dict, tickets: list) -> Dict:
    """Create Teams adaptive card notification"""
    
    status_icon = "✅" if result.get('status') == 'completed' else "❌"
    status_text = "Transfer Successful!" if result.get('status') == 'completed' else "Transfer Failed"
    
    return {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": status_text,
        "themeColor": "00FF00" if result.get('status') == 'completed' else "FF0000",
        "title": f"{status_icon} {status_text}",
        "sections": [
            {
                "facts": [
                    {"name": "User", "value": user_id},
                    {"name": "Bytes Transferred", "value": str(result.get('bytes_transferred', 0))},
                    {"name": "ServiceNow Ticket", "value": tickets[0] if tickets else "N/A"},
                    {"name": "Completed", "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
                ]
            }
        ],
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "View in ServiceNow",
                "targets": [
                    {
                        "os": "default",
                        "uri": f"https://your-instance.service-now.com/nav_to.do?uri=incident.do?sysparm_query=number={tickets[0]}"
                    }
                ]
            }
        ]
    }
