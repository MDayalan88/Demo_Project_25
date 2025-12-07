#!/usr/bin/env python3
"""
API Lambda Handler - Start Transfer
Triggers Step Functions workflow for file transfer
"""

import json
import boto3
import os
import time
from datetime import datetime

# Initialize clients
sfn_client = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')

# Configuration
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN', 'arn:aws:states:us-east-1:637423332185:stateMachine:FileFerry-TransferStateMachine')
TRANSFERS_TABLE = os.environ.get('TRANSFERS_TABLE', 'FileFerry-TransferRequests')

def lambda_handler(event, context):
    """
    POST /api/transfer
    Start a new file transfer
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Generate transfer ID
        transfer_id = f"tfr-{int(time.time())}"
        
        # Build Step Functions input
        sfn_input = {
            "transfer_id": transfer_id,
            "user_id": body.get('user_id', 'anonymous'),
            "request_type": "file_transfer",
            "source": body.get('source', {}),
            "destination": body.get('destination', {}),
            "options": body.get('options', {}),
            "servicenow": body.get('servicenow', {}),
            "notification": body.get('notification', {})
        }
        
        # Start Step Functions execution
        response = sfn_client.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=transfer_id,
            input=json.dumps(sfn_input)
        )
        
        execution_arn = response['executionArn']
        
        # Store in DynamoDB
        table = dynamodb.Table(TRANSFERS_TABLE)
        timestamp = int(time.time())
        table.put_item(
            Item={
                'transfer_id': transfer_id,
                'request_timestamp': timestamp,  # Add required sort key
                'user_id': sfn_input['user_id'],
                'status': 'RUNNING',
                'execution_arn': execution_arn,
                'source': json.dumps(sfn_input['source']),
                'destination': json.dumps(sfn_input['destination']),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'ttl': timestamp + (90 * 24 * 60 * 60)  # 90 days TTL
            }
        )
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'transfer_id': transfer_id,
                'execution_arn': execution_arn,
                'status': 'RUNNING',
                'message': 'Transfer started successfully'
            })
        }
    
    except Exception as e:
        print(f"Error starting transfer: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to start transfer'
            })
        }
