"""
Create All DynamoDB Tables for FileFerry AI Agent
Creates all 5 required DynamoDB tables with proper TTL, GSI, and encryption configuration
"""

import boto3
import time
import sys
from botocore.exceptions import ClientError

# Configuration
REGION = 'us-east-1'
BILLING_MODE = 'PAY_PER_REQUEST'  # On-demand pricing

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb', region_name=REGION)

def table_exists(table_name):
    """Check if table already exists"""
    try:
        dynamodb.describe_table(TableName=table_name)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return False
        raise

def create_active_sessions_table():
    """
    Table 1: ActiveSessions
    Purpose: SSO session management with 10-second TTL
    """
    table_name = 'FileFerry-ActiveSessions'
    
    if table_exists(table_name):
        print(f"✅ Table {table_name} already exists")
        return
    
    print(f"🔧 Creating {table_name}...")
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {'AttributeName': 'session_token', 'AttributeType': 'S'}
            ],
            KeySchema=[
                {'AttributeName': 'session_token', 'KeyType': 'HASH'}
            ],
            BillingMode=BILLING_MODE,
            SSESpecification={
                'Enabled': True,
                'SSEType': 'KMS'
            },
            Tags=[
                {'Key': 'Application', 'Value': 'FileFerry'},
                {'Key': 'Component', 'Value': 'SSO'},
                {'Key': 'TTL', 'Value': '10-seconds'}
            ]
        )
        
        # Wait for table to be active
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        # Enable TTL
        print(f"   Enabling TTL on {table_name}...")
        dynamodb.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'ttl'
            }
        )
        
        print(f"✅ Created {table_name} with 10-second TTL")
        
    except ClientError as e:
        print(f"❌ Error creating {table_name}: {e}")
        raise

def create_user_context_table():
    """
    Table 2: UserContext
    Purpose: Store conversation history and user context (30-day TTL)
    """
    table_name = 'FileFerry-UserContext'
    
    if table_exists(table_name):
        print(f"✅ Table {table_name} already exists")
        return
    
    print(f"🔧 Creating {table_name}...")
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            BillingMode=BILLING_MODE,
            SSESpecification={
                'Enabled': True,
                'SSEType': 'KMS'
            },
            Tags=[
                {'Key': 'Application', 'Value': 'FileFerry'},
                {'Key': 'Component', 'Value': 'Agent'},
                {'Key': 'TTL', 'Value': '30-days'}
            ]
        )
        
        # Wait for table to be active
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        # Enable TTL (30 days)
        print(f"   Enabling TTL on {table_name}...")
        dynamodb.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'ttl'
            }
        )
        
        print(f"✅ Created {table_name} with 30-day TTL")
        
    except ClientError as e:
        print(f"❌ Error creating {table_name}: {e}")
        raise

def create_transfer_requests_table():
    """
    Table 3: TransferRequests
    Purpose: Track all transfer requests with GSI on user_id (90-day TTL)
    """
    table_name = 'FileFerry-TransferRequests'
    
    if table_exists(table_name):
        print(f"✅ Table {table_name} already exists")
        return
    
    print(f"🔧 Creating {table_name}...")
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {'AttributeName': 'transfer_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'}
            ],
            KeySchema=[
                {'AttributeName': 'transfer_id', 'KeyType': 'HASH'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'UserIdIndex',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode=BILLING_MODE,
            SSESpecification={
                'Enabled': True,
                'SSEType': 'KMS'
            },
            Tags=[
                {'Key': 'Application', 'Value': 'FileFerry'},
                {'Key': 'Component', 'Value': 'Transfers'},
                {'Key': 'TTL', 'Value': '90-days'}
            ]
        )
        
        # Wait for table to be active
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        # Enable TTL (90 days)
        print(f"   Enabling TTL on {table_name}...")
        dynamodb.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'ttl'
            }
        )
        
        print(f"✅ Created {table_name} with 90-day TTL and GSI on user_id")
        
    except ClientError as e:
        print(f"❌ Error creating {table_name}: {e}")
        raise

def create_agent_learning_table():
    """
    Table 4: AgentLearning
    Purpose: Store ML predictions and learning data (no TTL - permanent)
    """
    table_name = 'FileFerry-AgentLearning'
    
    if table_exists(table_name):
        print(f"✅ Table {table_name} already exists")
        return
    
    print(f"🔧 Creating {table_name}...")
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {'AttributeName': 'transfer_type', 'AttributeType': 'S'},
                {'AttributeName': 'size_category', 'AttributeType': 'S'}
            ],
            KeySchema=[
                {'AttributeName': 'transfer_type', 'KeyType': 'HASH'},
                {'AttributeName': 'size_category', 'KeyType': 'RANGE'}
            ],
            BillingMode=BILLING_MODE,
            SSESpecification={
                'Enabled': True,
                'SSEType': 'KMS'
            },
            Tags=[
                {'Key': 'Application', 'Value': 'FileFerry'},
                {'Key': 'Component', 'Value': 'ML'},
                {'Key': 'TTL', 'Value': 'none'}
            ]
        )
        
        # Wait for table to be active
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        print(f"✅ Created {table_name} (no TTL - permanent storage)")
        
    except ClientError as e:
        print(f"❌ Error creating {table_name}: {e}")
        raise

def create_s3_file_cache_table():
    """
    Table 5: S3FileCache
    Purpose: Cache S3 file metadata (24-hour TTL)
    """
    table_name = 'FileFerry-S3FileCache'
    
    if table_exists(table_name):
        print(f"✅ Table {table_name} already exists")
        return
    
    print(f"🔧 Creating {table_name}...")
    
    try:
        response = dynamodb.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {'AttributeName': 'cache_key', 'AttributeType': 'S'}
            ],
            KeySchema=[
                {'AttributeName': 'cache_key', 'KeyType': 'HASH'}
            ],
            BillingMode=BILLING_MODE,
            SSESpecification={
                'Enabled': True,
                'SSEType': 'KMS'
            },
            Tags=[
                {'Key': 'Application', 'Value': 'FileFerry'},
                {'Key': 'Component', 'Value': 'Cache'},
                {'Key': 'TTL', 'Value': '24-hours'}
            ]
        )
        
        # Wait for table to be active
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        # Enable TTL (24 hours)
        print(f"   Enabling TTL on {table_name}...")
        dynamodb.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'ttl'
            }
        )
        
        print(f"✅ Created {table_name} with 24-hour TTL")
        
    except ClientError as e:
        print(f"❌ Error creating {table_name}: {e}")
        raise

def verify_all_tables():
    """Verify all tables are active and configured correctly"""
    print("\n🔍 Verifying all tables...")
    
    tables = [
        'FileFerry-ActiveSessions',
        'FileFerry-UserContext',
        'FileFerry-TransferRequests',
        'FileFerry-AgentLearning',
        'FileFerry-S3FileCache'
    ]
    
    for table_name in tables:
        try:
            response = dynamodb.describe_table(TableName=table_name)
            status = response['Table']['TableStatus']
            
            if status == 'ACTIVE':
                print(f"✅ {table_name}: {status}")
            else:
                print(f"⚠️  {table_name}: {status}")
                
        except ClientError as e:
            print(f"❌ {table_name}: NOT FOUND")

def main():
    """Create all DynamoDB tables"""
    print("=" * 70)
    print("FileFerry AI Agent - DynamoDB Infrastructure Setup")
    print("=" * 70)
    print(f"Region: {REGION}")
    print(f"Billing Mode: {BILLING_MODE}")
    print()
    
    try:
        # Create all tables
        create_active_sessions_table()
        time.sleep(2)
        
        create_user_context_table()
        time.sleep(2)
        
        create_transfer_requests_table()
        time.sleep(2)
        
        create_agent_learning_table()
        time.sleep(2)
        
        create_s3_file_cache_table()
        
        # Verify
        verify_all_tables()
        
        print("\n" + "=" * 70)
        print("✅ All DynamoDB tables created successfully!")
        print("=" * 70)
        print("\nTable Summary:")
        print("1. FileFerry-ActiveSessions    - SSO sessions (10-sec TTL)")
        print("2. FileFerry-UserContext       - Conversation history (30-day TTL)")
        print("3. FileFerry-TransferRequests  - Transfer tracking (90-day TTL, GSI)")
        print("4. FileFerry-AgentLearning     - ML predictions (permanent)")
        print("5. FileFerry-S3FileCache       - S3 metadata cache (24-hour TTL)")
        print("\nNext Steps:")
        print("1. Create IAM role: FileFerryReadOnlyRole")
        print("2. Implement ServiceNow Handler")
        print("3. Implement Transfer Handler")
        print("4. Create Step Functions workflow")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
