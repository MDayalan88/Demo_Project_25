"""
AWS Credentials Setup - No AWS CLI Required
Sets up credentials for FileFerry Agent
"""

import os
from pathlib import Path
import sys


def setup_credentials():
    """
    Interactive AWS credentials setup
    Creates .aws/credentials and .aws/config files
    """
    
    print("\n" + "="*70)
    print("🔐 FileFerry Agent - AWS Credentials Setup")
    print("="*70)
    print("\nThis script will configure your AWS credentials for FileFerry.")
    print("You'll need:")
    print("  • AWS Access Key ID")
    print("  • AWS Secret Access Key")
    print("  • AWS Region (default: us-east-1)")
    print("\n" + "="*70 + "\n")
    
    # Get credentials from user
    print("📝 Enter your AWS credentials:\n")
    
    access_key = input("AWS Access Key ID: ").strip()
    if not access_key:
        print("❌ Error: Access Key ID is required")
        return False
    
    secret_key = input("AWS Secret Access Key: ").strip()
    if not secret_key:
        print("❌ Error: Secret Access Key is required")
        return False
    
    region = input("AWS Region [us-east-1]: ").strip() or "us-east-1"
    
    print("\n" + "="*70)
    print("📦 Creating AWS configuration files...")
    print("="*70 + "\n")
    
    # Create .aws directory
    aws_dir = Path.home() / '.aws'
    aws_dir.mkdir(exist_ok=True)
    print(f"✅ Created directory: {aws_dir}")
    
    # Write credentials file
    credentials_file = aws_dir / 'credentials'
    with open(credentials_file, 'w') as f:
        f.write(f"[default]\n")
        f.write(f"aws_access_key_id = {access_key}\n")
        f.write(f"aws_secret_access_key = {secret_key}\n")
    
    # Set restrictive permissions (Windows)
    try:
        os.chmod(credentials_file, 0o600)
    except Exception:
        pass  # Windows permissions work differently
    
    print(f"✅ Created credentials: {credentials_file}")
    
    # Write config file
    config_file = aws_dir / 'config'
    with open(config_file, 'w') as f:
        f.write(f"[default]\n")
        f.write(f"region = {region}\n")
        f.write(f"output = json\n")
    
    print(f"✅ Created config: {config_file}")
    
    # Test credentials
    print("\n" + "="*70)
    print("🧪 Testing AWS credentials...")
    print("="*70 + "\n")
    
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        
        # Create STS client to verify credentials
        sts = boto3.client('sts', region_name=region)
        identity = sts.get_caller_identity()
        
        print("✅ AWS Credentials Valid!\n")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User ARN:   {identity['Arn']}")
        print(f"   Region:     {region}")
        
        # Test DynamoDB access
        print("\n🔍 Testing DynamoDB access...")
        dynamodb = boto3.client('dynamodb', region_name=region)
        
        try:
            response = dynamodb.list_tables(Limit=1)
            print(f"✅ DynamoDB access: OK")
            
            existing_tables = response.get('TableNames', [])
            if existing_tables:
                print(f"   Found {len(existing_tables)} existing table(s)")
            else:
                print(f"   No tables found (ready to create FileFerry tables)")
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                print(f"⚠️  DynamoDB access: Limited permissions")
                print(f"   You may need: dynamodb:ListTables permission")
            else:
                print(f"⚠️  DynamoDB error: {error_code}")
        
        # Test Bedrock access
        print("\n🔍 Testing Bedrock access...")
        try:
            bedrock = boto3.client('bedrock-runtime', region_name=region)
            # Just create client, don't invoke model yet
            print(f"✅ Bedrock client: OK")
            print(f"   ℹ️  Model access must be enabled in AWS Console")
            print(f"   Required: anthropic.claude-3-5-sonnet-20241022-v2:0")
        except Exception as e:
            print(f"⚠️  Bedrock error: {str(e)}")
        
        # Test S3 access
        print("\n🔍 Testing S3 access...")
        try:
            s3 = boto3.client('s3', region_name=region)
            response = s3.list_buckets()
            bucket_count = len(response.get('Buckets', []))
            print(f"✅ S3 access: OK")
            print(f"   Found {bucket_count} bucket(s)")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            print(f"⚠️  S3 error: {error_code}")
        
        print("\n" + "="*70)
        print("🎉 Setup Complete!")
        print("="*70)
        print("\n📋 Next Steps:")
        print("   1. Request Bedrock model access (if needed)")
        print("   2. Create DynamoDB tables:")
        print("      python infrastructure/create_dynamodb_tables.py")
        print("   3. Test components:")
        print("      python tests/test_components.py")
        print("\n")
        
        return True
        
    except NoCredentialsError:
        print("❌ Error: Credentials not found")
        print("   The credentials file was created but not loaded.")
        print("   Try restarting your terminal or IDE.")
        return False
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        
        print(f"❌ AWS Error: {error_code}")
        print(f"   {error_msg}")
        
        if error_code == 'InvalidClientTokenId':
            print("\n💡 Solution: Check your Access Key ID")
        elif error_code == 'SignatureDoesNotMatch':
            print("\n💡 Solution: Check your Secret Access Key")
        else:
            print(f"\n💡 Solution: Verify your AWS credentials are correct")
        
        return False
        
    except ImportError:
        print("❌ Error: boto3 not installed")
        print("\n💡 Solution: Run: pip install boto3")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


def main():
    """Main execution"""
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8+ required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    
    # Check boto3 installation
    try:
        import boto3
    except ImportError:
        print("❌ Error: boto3 not installed")
        print("\n💡 Run: pip install boto3")
        sys.exit(1)
    
    # Run setup
    success = setup_credentials()
    
    if success:
        sys.exit(0)
    else:
        print("\n❌ Setup failed. Please check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()