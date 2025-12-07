"""
DynamoDB Table Creation Script for FileFerry Agent
Follows AWS DynamoDB best practices (universal NoSQL patterns)
"""

import boto3
import sys
import argparse
from typing import Dict, List
from botocore.exceptions import ClientError


class FileFerryTableCreator:
    """
    Creates DynamoDB tables following NoSQL best practices
    """
    
    def __init__(self, region: str = 'us-east-1', profile: str = None):
        """
        Initialize table creator
        
        Args:
            region: AWS region
            profile: AWS profile name (optional)
        """
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        self.dynamodb = session.client('dynamodb', region_name=region)
        self.region = region
        
        print(f"🔧 Initialized DynamoDB client for region: {region}")
        if profile:
            print(f"📝 Using AWS profile: {profile}")
    
    def create_table(
        self,
        table_name: str,
        partition_key: Dict,
        sort_key: Dict = None,
        gsi_list: List[Dict] = None,
        ttl_attribute: str = None,
        billing_mode: str = 'PAY_PER_REQUEST'
    ) -> bool:
        """
        Create DynamoDB table with best practices
        
        Args:
            table_name: Table name
            partition_key: Partition key definition
            sort_key: Sort key definition (optional)
            gsi_list: Global secondary indexes (optional)
            ttl_attribute: TTL attribute name (optional)
            billing_mode: Billing mode (PAY_PER_REQUEST or PROVISIONED)
            
        Returns:
            True if successful
        """
        try:
            # Build key schema
            key_schema = [
                {
                    'AttributeName': partition_key['name'],
                    'KeyType': 'HASH'
                }
            ]
            
            attribute_definitions = [
                {
                    'AttributeName': partition_key['name'],
                    'AttributeType': partition_key['type']
                }
            ]
            
            # Add sort key if provided
            if sort_key:
                key_schema.append({
                    'AttributeName': sort_key['name'],
                    'KeyType': 'RANGE'
                })
                attribute_definitions.append({
                    'AttributeName': sort_key['name'],
                    'AttributeType': sort_key['type']
                })
            
            # Add GSI attributes if provided
            if gsi_list:
                for gsi in gsi_list:
                    for attr in gsi['attributes']:
                        if attr not in [a['AttributeName'] for a in attribute_definitions]:
                            attribute_definitions.append(attr)
            
            # Create table parameters
            table_params = {
                'TableName': table_name,
                'KeySchema': key_schema,
                'AttributeDefinitions': attribute_definitions,
                'BillingMode': billing_mode,
                'Tags': [
                    {'Key': 'Application', 'Value': 'FileFerry'},
                    {'Key': 'Environment', 'Value': 'Production'},
                    {'Key': 'ManagedBy', 'Value': 'Infrastructure-as-Code'}
                ]
            }
            
            # Add GSIs if provided
            if gsi_list:
                global_secondary_indexes = []
                for gsi in gsi_list:
                    global_secondary_indexes.append({
                        'IndexName': gsi['name'],
                        'KeySchema': gsi['key_schema'],
                        'Projection': gsi.get('projection', {'ProjectionType': 'ALL'})
                    })
                table_params['GlobalSecondaryIndexes'] = global_secondary_indexes
            
            # Create table
            print(f"\n📦 Creating table: {table_name}")
            print(f"   • Partition Key: {partition_key['name']} ({partition_key['type']})")
            if sort_key:
                print(f"   • Sort Key: {sort_key['name']} ({sort_key['type']})")
            if gsi_list:
                print(f"   • GSIs: {len(gsi_list)}")
            
            response = self.dynamodb.create_table(**table_params)
            
            # Wait for table to be active
            print(f"   ⏳ Waiting for table to become active...")
            waiter = self.dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            # Enable TTL if specified
            if ttl_attribute:
                print(f"   ⏰ Enabling TTL on attribute: {ttl_attribute}")
                self.dynamodb.update_time_to_live(
                    TableName=table_name,
                    TimeToLiveSpecification={
                        'Enabled': True,
                        'AttributeName': ttl_attribute
                    }
                )
            
            print(f"   ✅ Table created successfully: {table_name}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"   ℹ️  Table already exists: {table_name}")
                return True
            else:
                print(f"   ❌ Error creating table: {e}")
                return False
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return False
    
    def create_transfer_requests_table(self) -> bool:
        """
        Create TransferRequests table
        
        Best Practices Applied:
        - High cardinality partition key: user_id
        - Time-based sort key: request_timestamp
        - Embedded data: All transfer metadata in single item
        - TTL: 90 days automatic cleanup
        """
        return self.create_table(
            table_name='FileFerry-TransferRequests',
            partition_key={'name': 'user_id', 'type': 'S'},
            sort_key={'name': 'request_timestamp', 'type': 'S'},
            gsi_list=[
                {
                    'name': 'StatusIndex',
                    'key_schema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'},
                        {'AttributeName': 'request_timestamp', 'KeyType': 'RANGE'}
                    ],
                    'attributes': [
                        {'AttributeName': 'status', 'AttributeType': 'S'}
                    ],
                    'projection': {'ProjectionType': 'ALL'}
                }
            ],
            ttl_attribute='ttl_timestamp'
        )
    
    def create_agent_learning_table(self) -> bool:
        """
        Create AgentLearning table
        
        Best Practices Applied:
        - Partition key: file_size_category (predictable distribution)
        - Embedded: Historical transfer data for ML
        - No TTL: Learning data retained
        """
        return self.create_table(
            table_name='FileFerry-AgentLearning',
            partition_key={'name': 'file_size_category', 'type': 'S'},
            sort_key={'name': 'transfer_id', 'type': 'S'}
        )
    
    def create_user_context_table(self) -> bool:
        """
        Create UserContext table
        
        Best Practices Applied:
        - High cardinality partition key: user_id
        - Embedded: Conversation history in single item
        - TTL: 30 days conversation cleanup
        """
        return self.create_table(
            table_name='FileFerry-UserContext',
            partition_key={'name': 'user_id', 'type': 'S'},
            sort_key={'name': 'context_timestamp', 'type': 'S'},
            ttl_attribute='ttl_timestamp'
        )
    
    def create_active_sessions_table(self) -> bool:
        """
        Create ActiveSessions table
        
        Best Practices Applied:
        - High cardinality partition key: session_id (UUID)
        - Embedded: Session state in single item
        - TTL: 1 hour automatic session cleanup
        """
        return self.create_table(
            table_name='FileFerry-ActiveSessions',
            partition_key={'name': 'session_id', 'type': 'S'},
            ttl_attribute='ttl_timestamp'
        )
    
    def create_s3_file_cache_table(self) -> bool:
        """
        Create S3FileCache table
        
        Best Practices Applied:
        - Hierarchical Partition Key: bucket_name + file_key
        - Embedded: All S3 metadata in single item
        - TTL: 24 hours cache invalidation
        """
        return self.create_table(
            table_name='FileFerry-S3FileCache',
            partition_key={'name': 'cache_key', 'type': 'S'},  # Format: bucket#key
            sort_key={'name': 'cached_timestamp', 'type': 'S'},
            ttl_attribute='ttl_timestamp'
        )
    
    def verify_tables(self) -> bool:
        """
        Verify all tables exist and are active
        
        Returns:
            True if all tables verified
        """
        print("\n🔍 Verifying tables...")
        
        expected_tables = [
            'FileFerry-TransferRequests',
            'FileFerry-AgentLearning',
            'FileFerry-UserContext',
            'FileFerry-ActiveSessions',
            'FileFerry-S3FileCache'
        ]
        
        try:
            response = self.dynamodb.list_tables()
            existing_tables = response['TableNames']
            
            all_exist = True
            for table_name in expected_tables:
                if table_name in existing_tables:
                    # Check table status
                    table_info = self.dynamodb.describe_table(TableName=table_name)
                    status = table_info['Table']['TableStatus']
                    item_count = table_info['Table']['ItemCount']
                    
                    print(f"   ✅ {table_name}")
                    print(f"      Status: {status} | Items: {item_count}")
                    
                    # Check TTL if applicable
                    if table_name != 'FileFerry-AgentLearning':
                        try:
                            ttl_info = self.dynamodb.describe_time_to_live(TableName=table_name)
                            ttl_status = ttl_info['TimeToLiveDescription']['TimeToLiveStatus']
                            if ttl_status == 'ENABLED':
                                ttl_attr = ttl_info['TimeToLiveDescription']['AttributeName']
                                print(f"      TTL: {ttl_status} ({ttl_attr})")
                        except Exception:
                            pass
                else:
                    print(f"   ❌ {table_name} - NOT FOUND")
                    all_exist = False
            
            return all_exist
            
        except ClientError as e:
            print(f"   ❌ Error verifying tables: {e}")
            return False
    
    def create_all_tables(self) -> bool:
        """
        Create all FileFerry tables
        
        Returns:
            True if all tables created successfully
        """
        print("\n" + "="*70)
        print("🚀 FileFerry DynamoDB Table Creation")
        print("="*70)
        print("Following NoSQL Best Practices:")
        print("  • High cardinality partition keys")
        print("  • Embedded related data")
        print("  • TTL for automatic cleanup")
        print("  • Hierarchical partition keys (HPK)")
        print("="*70)
        
        tables_created = []
        
        # Create tables
        if self.create_transfer_requests_table():
            tables_created.append('TransferRequests')
        
        if self.create_agent_learning_table():
            tables_created.append('AgentLearning')
        
        if self.create_user_context_table():
            tables_created.append('UserContext')
        
        if self.create_active_sessions_table():
            tables_created.append('ActiveSessions')
        
        if self.create_s3_file_cache_table():
            tables_created.append('S3FileCache')
        
        # Verify all tables
        success = self.verify_tables()
        
        print("\n" + "="*70)
        if success:
            print("✅ All tables created and verified successfully!")
            print(f"   Tables: {len(tables_created)}/5")
        else:
            print("⚠️  Some tables failed to create or verify")
        print("="*70 + "\n")
        
        return success


def main():
    """Main execution with proper argument parsing"""
    
    parser = argparse.ArgumentParser(
        description='Create FileFerry DynamoDB tables following NoSQL best practices',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python infrastructure/create_dynamodb_tables.py
  python infrastructure/create_dynamodb_tables.py --region us-west-2
  python infrastructure/create_dynamodb_tables.py --region us-east-1 --profile prod
        """
    )
    
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    
    parser.add_argument(
        '--profile',
        default=None,
        help='AWS profile name (optional)'
    )
    
    args = parser.parse_args()
    
    print(f"\n🎯 Configuration:")
    print(f"   Region: {args.region}")
    if args.profile:
        print(f"   Profile: {args.profile}")
    
    # Create tables
    try:
        creator = FileFerryTableCreator(region=args.region, profile=args.profile)
        success = creator.create_all_tables()
        
        if success:
            print("📋 Next Steps:")
            print("   1. Verify tables in AWS Console")
            print("   2. Run: python setup_aws_credentials.py (if not done)")
            print("   3. Test agent: python tests/test_components.py")
            print("   4. Deploy Lambda function")
            sys.exit(0)
        else:
            print("❌ Table creation failed. Check errors above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("   1. Check AWS credentials: aws sts get-caller-identity")
        print("   2. Verify IAM permissions for DynamoDB")
        print("   3. Ensure region is valid: aws ec2 describe-regions")
        sys.exit(1)


if __name__ == "__main__":
    main()