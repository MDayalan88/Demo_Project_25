"""
Test FileFerry DynamoDB Tables
Validates table access and basic operations
"""

import boto3
import sys
from datetime import datetime, timedelta
from decimal import Decimal
import json


def test_transfer_requests_table():
    """Test TransferRequests table"""
    print("\n" + "="*70)
    print("🧪 Testing FileFerry-TransferRequests Table")
    print("="*70)
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('FileFerry-TransferRequests')
    
    # Test data
    now = datetime.utcnow()
    ttl_timestamp = int((now + timedelta(days=90)).timestamp())
    
    test_item = {
        'user_id': 'martin.dayalan@company.com',
        'request_timestamp': now.isoformat(),
        'transfer_id': 'test-transfer-001',
        'status': 'completed',
        'file_info': {
            'bucket': 'prod-bucket',
            'key': 'reports/Q4_2024.csv',
            'size_mb': Decimal('25.5')
        },
        'destination': {
            'type': 'sftp',
            'host': 'ftp.example.com',
            'path': '/incoming/'
        },
        'prediction': {
            'success_rate': Decimal('0.94'),
            'estimated_seconds': 120
        },
        'tickets': ['INC001', 'INC002'],
        'ttl_timestamp': ttl_timestamp
    }
    
    try:
        # 1. Write item
        print("\n📝 Writing test transfer request...")
        table.put_item(Item=test_item)
        print("   ✅ Write successful")
        
        # 2. Read item back
        print("\n📖 Reading transfer request...")
        response = table.get_item(
            Key={
                'user_id': test_item['user_id'],
                'request_timestamp': test_item['request_timestamp']
            }
        )
        
        if 'Item' in response:
            print("   ✅ Read successful")
            print(f"   Transfer ID: {response['Item']['transfer_id']}")
            print(f"   Status: {response['Item']['status']}")
            print(f"   File: {response['Item']['file_info']['bucket']}/{response['Item']['file_info']['key']}")
            print(f"   TTL: {response['Item']['ttl_timestamp']} (90 days)")
        
        # 3. Query by user
        print("\n🔍 Querying transfers by user...")
        response = table.query(
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={
                ':uid': test_item['user_id']
            }
        )
        print(f"   ✅ Found {response['Count']} transfer(s)")
        
        # 4. Query by status (GSI)
        print("\n🔍 Querying transfers by status (using StatusIndex GSI)...")
        response = table.query(
            IndexName='StatusIndex',
            KeyConditionExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'completed'}
        )
        print(f"   ✅ Found {response['Count']} completed transfer(s)")
        
        # 5. Cleanup
        print("\n🧹 Cleaning up test data...")
        table.delete_item(
            Key={
                'user_id': test_item['user_id'],
                'request_timestamp': test_item['request_timestamp']
            }
        )
        print("   ✅ Cleanup complete")
        
        print("\n✅ TransferRequests table: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_agent_learning_table():
    """Test AgentLearning table"""
    print("\n" + "="*70)
    print("🧪 Testing FileFerry-AgentLearning Table")
    print("="*70)
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('FileFerry-AgentLearning')
    
    test_item = {
        'file_size_category': 'large',  # small/medium/large/xlarge
        'transfer_id': 'learning-test-001',
        'file_size_mb': Decimal('250.5'),
        'destination_type': 'sftp',
        'success': True,
        'duration_seconds': 180,
        'timestamp': datetime.utcnow().isoformat(),
        'error_code': None
    }
    
    try:
        print("\n📝 Writing learning data...")
        table.put_item(Item=test_item)
        print("   ✅ Write successful")
        
        print("\n📖 Reading learning data...")
        response = table.get_item(
            Key={
                'file_size_category': test_item['file_size_category'],
                'transfer_id': test_item['transfer_id']
            }
        )
        
        if 'Item' in response:
            print("   ✅ Read successful")
            print(f"   Category: {response['Item']['file_size_category']}")
            print(f"   Success: {response['Item']['success']}")
            print(f"   Duration: {response['Item']['duration_seconds']}s")
        
        print("\n🔍 Querying by file size category...")
        response = table.query(
            KeyConditionExpression='file_size_category = :cat',
            ExpressionAttributeValues={':cat': 'large'}
        )
        print(f"   ✅ Found {response['Count']} large file transfer(s)")
        
        print("\n🧹 Cleaning up...")
        table.delete_item(
            Key={
                'file_size_category': test_item['file_size_category'],
                'transfer_id': test_item['transfer_id']
            }
        )
        print("   ✅ Cleanup complete")
        
        print("\n✅ AgentLearning table: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def test_s3_file_cache_table():
    """Test S3FileCache table (Hierarchical Partition Key)"""
    print("\n" + "="*70)
    print("🧪 Testing FileFerry-S3FileCache Table (HPK)")
    print("="*70)
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('FileFerry-S3FileCache')
    
    now = datetime.utcnow()
    ttl_timestamp = int((now + timedelta(hours=24)).timestamp())
    
    # Hierarchical Partition Key: bucket#key
    test_item = {
        'cache_key': 'prod-bucket#reports/Q4_2024.csv',  # HPK format
        'cached_timestamp': now.isoformat(),
        'bucket': 'prod-bucket',
        'key': 'reports/Q4_2024.csv',
        'size_bytes': 26738688,
        'size_mb': Decimal('25.5'),
        'last_modified': (now - timedelta(days=2)).isoformat(),
        'content_type': 'text/csv',
        'storage_class': 'STANDARD',
        'encryption': 'AES256',
        'etag': 'abc123def456',
        'ttl_timestamp': ttl_timestamp
    }
    
    try:
        print("\n📝 Writing cache entry with HPK...")
        print(f"   Cache Key: {test_item['cache_key']}")
        table.put_item(Item=test_item)
        print("   ✅ Write successful")
        
        print("\n📖 Reading cache entry...")
        response = table.get_item(
            Key={
                'cache_key': test_item['cache_key'],
                'cached_timestamp': test_item['cached_timestamp']
            }
        )
        
        if 'Item' in response:
            print("   ✅ Read successful")
            print(f"   Bucket: {response['Item']['bucket']}")
            print(f"   Key: {response['Item']['key']}")
            print(f"   Size: {response['Item']['size_mb']} MB")
            print(f"   TTL: {response['Item']['ttl_timestamp']} (24 hours)")
        
        print("\n🔍 Querying by cache_key (HPK)...")
        response = table.query(
            KeyConditionExpression='cache_key = :ck',
            ExpressionAttributeValues={':ck': test_item['cache_key']}
        )
        print(f"   ✅ Found {response['Count']} cached file(s)")
        
        print("\n🧹 Cleaning up...")
        table.delete_item(
            Key={
                'cache_key': test_item['cache_key'],
                'cached_timestamp': test_item['cached_timestamp']
            }
        )
        print("   ✅ Cleanup complete")
        
        print("\n✅ S3FileCache table: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


def verify_table_configuration():
    """Verify table configuration and TTL settings"""
    print("\n" + "="*70)
    print("🔍 Verifying Table Configuration")
    print("="*70)
    
    client = boto3.client('dynamodb')
    
    tables = [
        'FileFerry-TransferRequests',
        'FileFerry-AgentLearning',
        'FileFerry-UserContext',
        'FileFerry-ActiveSessions',
        'FileFerry-S3FileCache'
    ]
    
    for table_name in tables:
        try:
            # Check table details
            table_info = client.describe_table(TableName=table_name)
            status = table_info['Table']['TableStatus']
            item_count = table_info['Table']['ItemCount']
            billing_mode = table_info['Table']['BillingModeSummary']['BillingMode']
            
            print(f"\n✅ {table_name}")
            print(f"   Status: {status}")
            print(f"   Items: {item_count}")
            print(f"   Billing: {billing_mode}")
            
            # Check partition key
            key_schema = table_info['Table']['KeySchema']
            partition_key = [k for k in key_schema if k['KeyType'] == 'HASH'][0]
            print(f"   Partition Key: {partition_key['AttributeName']}")
            
            # Check sort key
            sort_keys = [k for k in key_schema if k['KeyType'] == 'RANGE']
            if sort_keys:
                print(f"   Sort Key: {sort_keys[0]['AttributeName']}")
            
            # Check GSIs
            if 'GlobalSecondaryIndexes' in table_info['Table']:
                gsi_count = len(table_info['Table']['GlobalSecondaryIndexes'])
                print(f"   GSIs: {gsi_count}")
            
            # Check TTL
            if table_name != 'FileFerry-AgentLearning':
                try:
                    ttl_info = client.describe_time_to_live(TableName=table_name)
                    ttl_status = ttl_info['TimeToLiveDescription']['TimeToLiveStatus']
                    if ttl_status == 'ENABLED':
                        ttl_attr = ttl_info['TimeToLiveDescription']['AttributeName']
                        print(f"   TTL: {ttl_status} ({ttl_attr})")
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"\n❌ {table_name}: Error - {str(e)}")
    
    print("\n✅ Configuration verification complete")


def main():
    """Run all tests"""
    print("\n" + "🎯"*35)
    print("FileFerry DynamoDB Tables - Integration Tests")
    print("🎯"*35)
    
    results = []
    
    # Configuration check
    verify_table_configuration()
    
    # Functional tests
    results.append(("TransferRequests", test_transfer_requests_table()))
    results.append(("AgentLearning", test_agent_learning_table()))
    results.append(("S3FileCache (HPK)", test_s3_file_cache_table()))
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for table_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status} - {table_name}")
    
    print("\n" + "="*70)
    if passed == total:
        print(f"🎉 All {total} tests PASSED!")
        print("="*70)
        print("\n📋 Next Steps:")
        print("   1. Enable Bedrock model access:")
        print("      AWS Console → Bedrock → Model access")
        print("      Request: anthropic.claude-3-5-sonnet-20241022-v2:0")
        print("\n   2. Test agent with real AI:")
        print("      python test_agent_bedrock.py")
        print("\n   3. Deploy to Lambda:")
        print("      python infrastructure/deploy_lambda.py")
        print("\n")
        return 0
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("="*70 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())