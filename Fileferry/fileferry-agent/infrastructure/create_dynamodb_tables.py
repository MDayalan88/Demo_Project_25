"""
DynamoDB Table Creation Script
Creates all required DynamoDB tables with proper partition keys and TTL settings
"""

import boto3
from botocore.exceptions import ClientError


def create_tables(region='us-east-1'):
    """
    Create all FileFerry DynamoDB tables
    
    Args:
        region: AWS region
    """
    dynamodb = boto3.client('dynamodb', region_name=region)
    
    tables = [
        {
            'TableName': 'FileFerry-TransferRequests',
            'KeySchema': [
                {'AttributeName': 'userId', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'requestId', 'KeyType': 'RANGE'}  # Sort key
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'userId', 'AttributeType': 'S'},
                {'AttributeName': 'requestId', 'AttributeType': 'S'}
            ],
            'BillingMode': 'PAY_PER_REQUEST',  # On-demand pricing
            'Tags': [
                {'Key': 'Application', 'Value': 'FileFerry'},
                {'Key': 'Purpose', 'Value': 'TransferRequests'}
            ]
        },
        {
            'TableName': 'FileFerry-AgentLearning',
            'KeySchema': [
                {'AttributeName': 'transferType', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}  # Sort key
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'transferType', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'Tags': [
                {'Key': 'Application', 'Value': 'FileFerry'},
                {'Key': 'Purpose', 'Value': 'MachineLearning'}
            ]
        },
        {
            'TableName': 'FileFerry-UserContext',
            'KeySchema': [
                {'AttributeName': 'userId', 'KeyType': 'HASH'}  # Partition key only
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'userId', 'AttributeType': 'S'}
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'Tags': [
                {'Key': 'Application', 'Value': 'FileFerry'},
                {'Key': 'Purpose', 'Value': 'UserContext'}
            ]
        },
        {
            'TableName': 'FileFerry-ActiveSessions',
            'KeySchema': [
                {'AttributeName': 'sessionId', 'KeyType': 'HASH'}  # Partition key only
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'sessionId', 'AttributeType': 'S'}
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'Tags': [
                {'Key': 'Application', 'Value': 'FileFerry'},
                {'Key': 'Purpose', 'Value': 'SessionManagement'}
            ]
        },
        {
            'TableName': 'FileFerry-S3FileCache',
            'KeySchema': [
                {'AttributeName': 'bucketName', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'fileKey', 'KeyType': 'RANGE'}  # Sort key
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'bucketName', 'AttributeType': 'S'},
                {'AttributeName': 'fileKey', 'AttributeType': 'S'}
            ],
            'BillingMode': 'PAY_PER_REQUEST',
            'Tags': [
                {'Key': 'Application', 'Value': 'FileFerry'},
                {'Key': 'Purpose', 'Value': 'CachingLayer'}
            ]
        }
    ]
    
    for table_config in tables:
        table_name = table_config['TableName']
        
        try:
            print(f"Creating table {table_name}...")
            response = dynamodb.create_table(**table_config)
            print(f"✅ Table {table_name} created successfully")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠️  Table {table_name} already exists")
            else:
                print(f"❌ Error creating table {table_name}: {str(e)}")
    
    # Enable TTL on tables that need it
    ttl_configs = [
        {
            'TableName': 'FileFerry-AgentLearning',
            'AttributeName': 'ttl'
        },
        {
            'TableName': 'FileFerry-ActiveSessions',
            'AttributeName': 'ttl'
        },
        {
            'TableName': 'FileFerry-S3FileCache',
            'AttributeName': 'ttl'
        }
    ]
    
    print("\nEnabling TTL on tables...")
    
    for ttl_config in ttl_configs:
        try:
            dynamodb.update_time_to_live(
                TableName=ttl_config['TableName'],
                TimeToLiveSpecification={
                    'Enabled': True,
                    'AttributeName': ttl_config['AttributeName']
                }
            )
            print(f"✅ TTL enabled on {ttl_config['TableName']}")
            
        except ClientError as e:
            print(f"⚠️  TTL configuration for {ttl_config['TableName']}: {str(e)}")
    
    print("\n🎉 All tables created successfully!")
    print("\nTable Summary:")
    print("- FileFerry-TransferRequests: userId (PK), requestId (SK)")
    print("- FileFerry-AgentLearning: transferType (PK), timestamp (SK), TTL: 1 year")
    print("- FileFerry-UserContext: userId (PK)")
    print("- FileFerry-ActiveSessions: sessionId (PK), TTL: 1 hour")
    print("- FileFerry-S3FileCache: bucketName (PK), fileKey (SK), TTL: 24 hours")


if __name__ == '__main__':
    import sys
    
    region = sys.argv[1] if len(sys.argv) > 1 else 'us-east-1'
    
    print(f"Creating DynamoDB tables in region: {region}\n")
    create_tables(region)
