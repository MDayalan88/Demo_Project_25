#!/usr/bin/env python3
"""
API Lambda Handler - Get Transfer Status
Retrieves status of a file transfer from Step Functions and DynamoDB
"""

import json
import boto3
import os

# Initialize clients
sfn_client = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')

# Configuration
TRANSFERS_TABLE = os.environ.get('TRANSFERS_TABLE', 'FileFerry-TransferRequests')

def lambda_handler(event, context):
    """
    GET /api/transfer/{transfer_id}
    Get status of a specific transfer
    """
    try:
        # Get transfer_id from path parameters
        transfer_id = event.get('pathParameters', {}).get('transfer_id')
        
        if not transfer_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': False, 'error': 'Missing transfer_id'})
            }
        
        # Get from DynamoDB
        table = dynamodb.Table(TRANSFERS_TABLE)
        response = table.get_item(Key={'transfer_id': transfer_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': False, 'error': 'Transfer not found'})
            }
        
        item = response['Item']
        execution_arn = item.get('execution_arn')
        
        # Get execution status from Step Functions
        if execution_arn:
            try:
                exec_response = sfn_client.describe_execution(executionArn=execution_arn)
                status = exec_response['status']
                
                # Update DynamoDB if status changed
                if status != item.get('status'):
                    table.update_item(
                        Key={'transfer_id': transfer_id},
                        UpdateExpression='SET #status = :status',
                        ExpressionAttributeNames={'#status': 'status'},
                        ExpressionAttributeValues={':status': status}
                    )
                    item['status'] = status
            except:
                pass
        
        # Return transfer details
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'transfer_id': transfer_id,
                'status': item.get('status', 'UNKNOWN'),
                'user_id': item.get('user_id'),
                'source': json.loads(item.get('source', '{}')),
                'destination': json.loads(item.get('destination', '{}')),
                'created_at': item.get('created_at'),
                'updated_at': item.get('updated_at'),
                'execution_arn': execution_arn
            })
        }
    
    except Exception as e:
        print(f"Error getting transfer status: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': False, 'error': str(e)})
        }
