"""
Automated IAM permission fixer for FileFerry
Grants necessary DynamoDB permissions to IAM user
Works without AWS CLI - uses boto3 directly
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError, NoCredentialsError


def fix_iam_permissions(user_name: str = "Fileferry", account_id: str = "637423332185"):
    """
    Add DynamoDB permissions to IAM user
    
    Args:
        user_name: IAM user name (default: Fileferry)
        account_id: AWS account ID
    """
    
    print("\n" + "="*70)
    print(f"🔐 FileFerry IAM Permission Fixer")
    print("="*70)
    print(f"   User: {user_name}")
    print(f"   Account: {account_id}")
    print("="*70 + "\n")
    
    try:
        # Create IAM client
        iam = boto3.client('iam')
        
        # Verify user exists
        print(f"🔍 Verifying IAM user exists...")
        try:
            iam.get_user(UserName=user_name)
            print(f"   ✅ User found: {user_name}\n")
        except iam.exceptions.NoSuchEntityException:
            print(f"   ❌ Error: User '{user_name}' not found")
            print(f"\n💡 Solution:")
            print(f"   1. Check username: aws iam list-users")
            print(f"   2. Or create user in AWS Console → IAM → Users")
            return False
        
        # Define comprehensive policy for FileFerry
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "DynamoDBTableManagement",
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:CreateTable",
                        "dynamodb:DescribeTable",
                        "dynamodb:UpdateTable",
                        "dynamodb:DeleteTable",
                        "dynamodb:ListTables",
                        "dynamodb:DescribeTimeToLive",
                        "dynamodb:UpdateTimeToLive",
                        "dynamodb:TagResource",
                        "dynamodb:UntagResource",
                        "dynamodb:ListTagsOfResource"
                    ],
                    "Resource": [
                        f"arn:aws:dynamodb:*:{account_id}:table/FileFerry-*"
                    ]
                },
                {
                    "Sid": "DynamoDBListAll",
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:ListTables",
                        "dynamodb:DescribeLimits"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "DynamoDBDataAccess",
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                        "dynamodb:BatchGetItem",
                        "dynamodb:BatchWriteItem"
                    ],
                    "Resource": [
                        f"arn:aws:dynamodb:*:{account_id}:table/FileFerry-*",
                        f"arn:aws:dynamodb:*:{account_id}:table/FileFerry-*/index/*"
                    ]
                },
                {
                    "Sid": "BedrockModelAccess",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": [
                        "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
                        "arn:aws:bedrock:*::foundation-model/anthropic.*"
                    ]
                },
                {
                    "Sid": "S3ReadAccess",
                    "Effect": "Allow",
                    "Action": [
                        "s3:ListAllMyBuckets",
                        "s3:ListBucket",
                        "s3:GetObject",
                        "s3:GetObjectMetadata",
                        "s3:GetBucketLocation"
                    ],
                    "Resource": [
                        "arn:aws:s3:::*"
                    ]
                },
                {
                    "Sid": "StepFunctionsExecution",
                    "Effect": "Allow",
                    "Action": [
                        "states:StartExecution",
                        "states:DescribeExecution",
                        "states:GetExecutionHistory"
                    ],
                    "Resource": [
                        f"arn:aws:states:*:{account_id}:stateMachine:FileFerry-*",
                        f"arn:aws:states:*:{account_id}:execution:FileFerry-*:*"
                    ]
                },
                {
                    "Sid": "XRayTracing",
                    "Effect": "Allow",
                    "Action": [
                        "xray:PutTraceSegments",
                        "xray:PutTelemetryRecords"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "CloudWatchLogs",
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": f"arn:aws:logs:*:{account_id}:log-group:/aws/lambda/FileFerry-*"
                }
            ]
        }
        
        policy_name = "FileFerryFullAccess"
        
        # Check if policy already exists
        print(f"🔍 Checking for existing policy...")
        try:
            existing_policy = iam.get_user_policy(
                UserName=user_name,
                PolicyName=policy_name
            )
            print(f"   ℹ️  Policy already exists: {policy_name}")
            print(f"   🔄 Updating policy with latest permissions...\n")
        except iam.exceptions.NoSuchEntityException:
            print(f"   ℹ️  No existing policy found")
            print(f"   📝 Creating new policy: {policy_name}\n")
        
        # Add/Update inline policy
        print(f"📝 Applying IAM policy...")
        iam.put_user_policy(
            UserName=user_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document, indent=2)
        )
        
        print(f"✅ Policy applied successfully!\n")
        
        # Display granted permissions
        print("="*70)
        print("📋 Granted Permissions:")
        print("="*70)
        print("\n✅ DynamoDB:")
        print("   • CreateTable, DescribeTable, UpdateTable, DeleteTable")
        print("   • ListTables, UpdateTimeToLive")
        print("   • PutItem, GetItem, UpdateItem, DeleteItem")
        print("   • Query, Scan, BatchGetItem, BatchWriteItem")
        print("   • Resource: arn:aws:dynamodb:*:*:table/FileFerry-*")
        
        print("\n✅ AWS Bedrock:")
        print("   • InvokeModel (Claude 3.5 Sonnet)")
        print("   • Model: anthropic.claude-3-5-sonnet-20241022-v2:0")
        
        print("\n✅ Amazon S3:")
        print("   • ListBucket, GetObject (Read-only)")
        print("   • All buckets accessible")
        
        print("\n✅ Step Functions:")
        print("   • StartExecution, DescribeExecution")
        print("   • Resource: FileFerry-* state machines")
        
        print("\n✅ AWS X-Ray:")
        print("   • PutTraceSegments (Distributed tracing)")
        
        print("\n✅ CloudWatch Logs:")
        print("   • CreateLogGroup, PutLogEvents")
        print("   • Resource: /aws/lambda/FileFerry-*")
        
        print("\n" + "="*70)
        print("🎉 IAM Permissions Fixed Successfully!")
        print("="*70)
        
        print("\n📋 Next Steps:")
        print("   1. Retry DynamoDB table creation:")
        print("      python infrastructure/create_dynamodb_tables.py --region us-east-1")
        print("\n   2. Test component access:")
        print("      python tests/test_components.py")
        print("\n   3. Request Bedrock model access:")
        print("      AWS Console → Bedrock → Model access")
        print("\n")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        
        print(f"\n❌ AWS Error: {error_code}")
        print(f"   {error_msg}\n")
        
        if error_code == 'AccessDenied':
            print("💡 Solution:")
            print("   Your current AWS credentials don't have permission to modify IAM policies.")
            print("\n   Options:")
            print("   1. Ask your AWS administrator to grant you IAM permissions")
            print("   2. Or ask admin to add the FileFerryFullAccess policy to user 'Fileferry'")
            print("   3. Or use administrator credentials temporarily")
            print("\n   Required IAM permission:")
            print("   • iam:PutUserPolicy")
            print("   • iam:GetUser")
            
        elif error_code == 'InvalidClientTokenId':
            print("💡 Solution:")
            print("   Your AWS Access Key ID is invalid.")
            print("   Run: python setup_aws_credentials.py")
            
        elif error_code == 'SignatureDoesNotMatch':
            print("💡 Solution:")
            print("   Your AWS Secret Access Key is invalid.")
            print("   Run: python setup_aws_credentials.py")
            
        return False
        
    except NoCredentialsError:
        print("\n❌ Error: No AWS credentials found")
        print("\n💡 Solution:")
        print("   Run: python setup_aws_credentials.py")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("   1. Verify AWS credentials are configured")
        print("   2. Check IAM user exists in AWS Console")
        print("   3. Ensure you have sufficient permissions")
        return False


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fix IAM permissions for FileFerry user',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python infrastructure/fix_iam_permissions.py
  python infrastructure/fix_iam_permissions.py --user Fileferry
  python infrastructure/fix_iam_permissions.py --user MyUser --account 123456789012
        """
    )
    
    parser.add_argument(
        '--user',
        default='Fileferry',
        help='IAM user name (default: Fileferry)'
    )
    
    parser.add_argument(
        '--account',
        default='637423332185',
        help='AWS account ID (default: 637423332185)'
    )
    
    args = parser.parse_args()
    
    # Run fix
    success = fix_iam_permissions(args.user, args.account)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()