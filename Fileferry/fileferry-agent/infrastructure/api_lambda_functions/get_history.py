#!/usr/bin/env python3
"""
API Lambda Handler - Get Transfer History
Retrieves transfer history for a user from DynamoDB
"""

import json
import boto3
import os
from boto3.dynamodb.conditions import Key

# Initialize clients
dynamodb = boto3.resource('dynamodb')

# Configuration
TRANSFERS_TABLE = os.environ.get('TRANSFERS_TABLE', 'FileFerry-TransferRequests')

def lambda_handler(event, context):
    """
    GET /api/transfers?user_id={user_id}&limit={limit}
    Get transfer history for a user
    """
    try:
        # Get query parameters
        params = event.get('queryStringParameters', {}) or {}
        user_id = params.get('user_id')
        limit = int(params.get('limit', '20'))
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': False, 'error': 'Missing user_id parameter'})
            }
        
        # Query DynamoDB GSI by user_id
        table = dynamodb.Table(TRANSFERS_TABLE)
        response = table.query(
            IndexName='user_id-index',
            KeyConditionExpression=Key('user_id').eq(user_id),
            Limit=limit,
            ScanIndexForward=False  # Most recent first
        )
        
        items = response.get('Items', [])
        
        # Format response
        transfers = []
        for item in items:
            transfers.append({
                'transfer_id': item.get('transfer_id'),
                'status': item.get('status'),
                'source': json.loads(item.get('source', '{}')),
                'destination': json.loads(item.get('destination', '{}')),
                'created_at': item.get('created_at'),
                'updated_at': item.get('updated_at')
            })
        
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
                'user_id': user_id,
                'count': len(transfers),
                'transfers': transfers
            })
        }
    
    except Exception as e:
        print(f"Error getting transfer history: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': False, 'error': str(e)})
        }
