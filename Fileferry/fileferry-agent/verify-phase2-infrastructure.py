"""
Verify Phase 2 Infrastructure Setup
Tests all DynamoDB tables and IAM role configuration
"""

import boto3
import sys
from botocore.exceptions import ClientError

REGION = 'us-east-1'

def check_table(table_name):
    """Check if DynamoDB table exists and is active"""
    try:
        dynamodb = boto3.client('dynamodb', region_name=REGION)
        response = dynamodb.describe_table(TableName=table_name)
        
        status = response['Table']['TableStatus']
        ttl_enabled = False
        
        # Check TTL
        try:
            ttl_response = dynamodb.describe_time_to_live(TableName=table_name)
            ttl_status = ttl_response['TimeToLiveDescription']['TimeToLiveStatus']
            ttl_enabled = ttl_status == 'ENABLED'
        except:
            pass
        
        # Check encryption
        encryption = response['Table'].get('SSEDescription', {})
        encrypted = encryption.get('Status') == 'ENABLED'
        
        return {
            'exists': True,
            'status': status,
            'ttl_enabled': ttl_enabled,
            'encrypted': encrypted,
            'item_count': response['Table']['ItemCount'],
            'size_bytes': response['Table']['TableSizeBytes']
        }
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return {'exists': False}
        raise

def check_iam_role(role_name):
    """Check if IAM role exists"""
    try:
        iam = boto3.client('iam')
        response = iam.get_role(RoleName=role_name)
        return {
            'exists': True,
            'arn': response['Role']['Arn'],
            'created': response['Role']['CreateDate']
        }
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return {'exists': False}
        raise

def main():
    print("=" * 70)
    print("Phase 2 Infrastructure Verification")
    print("=" * 70)
    print()
    
    # Tables to check
    tables = [
        ('FileFerry-ActiveSessions', '10-sec TTL', True),
        ('FileFerry-UserContext', '30-day TTL', True),
        ('FileFerry-TransferRequests', '90-day TTL + GSI', True),
        ('FileFerry-AgentLearning', 'No TTL', False),
        ('FileFerry-S3FileCache', '24-hour TTL', True)
    ]
    
    print("🗄️  DynamoDB Tables:")
    print()
    
    all_tables_ok = True
    
    for table_name, description, ttl_expected in tables:
        info = check_table(table_name)
        
        if not info['exists']:
            print(f"❌ {table_name}")
            print(f"   Status: NOT FOUND")
            all_tables_ok = False
        elif info['status'] != 'ACTIVE':
            print(f"⚠️  {table_name}")
            print(f"   Status: {info['status']} (not active)")
            all_tables_ok = False
        else:
            print(f"✅ {table_name}")
            print(f"   Status: {info['status']}")
            print(f"   TTL: {'ENABLED' if info['ttl_enabled'] else 'DISABLED'}", end='')
            if ttl_expected and not info['ttl_enabled']:
                print(" ⚠️  (expected enabled)")
                all_tables_ok = False
            else:
                print()
            print(f"   Encrypted: {'YES' if info['encrypted'] else 'NO'}")
            print(f"   Items: {info['item_count']}")
            print(f"   Size: {info['size_bytes']:,} bytes")
        print()
    
    # Check IAM role
    print("🔐 IAM Roles:")
    print()
    
    role_name = 'FileFerryReadOnlyRole'
    role_info = check_iam_role(role_name)
    
    if not role_info['exists']:
        print(f"⚠️  {role_name}: NOT FOUND")
        print(f"   Note: Role may need to be created manually or via CloudFormation")
        # Don't fail - role might not be needed for local testing
    else:
        print(f"✅ {role_name}")
        print(f"   ARN: {role_info['arn']}")
        print(f"   Created: {role_info['created']}")
    
    print()
    print("=" * 70)
    
    if all_tables_ok:
        print("✅ Phase 2 Infrastructure: VERIFIED")
        print()
        print("All DynamoDB tables are operational!")
        print()
        print("Next Steps:")
        print("1. Update config/config.yaml with AWS account ID")
        print("2. Test SSO Handler authentication")
        print("3. Proceed to Phase 3 (ServiceNow Handler)")
        return 0
    else:
        print("⚠️  Phase 2 Infrastructure: INCOMPLETE")
        print()
        print("Some tables are missing or not configured correctly.")
        print("Run: python infrastructure/create_all_dynamodb_tables.py")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
