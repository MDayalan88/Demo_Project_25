"""
IAM Bedrock Permissions Checker and Fixer
Uses boto3 (no AWS CLI required)
"""

import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError

def main():
    print("=" * 60)
    print("Checking and Fixing IAM Bedrock Permissions (Python)")
    print("=" * 60)
    print()
    
    try:
        # Step 1: Get current IAM identity
        print("1. Getting current IAM identity...")
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        user_arn = identity['Arn']
        account_id = identity['Account']
        user_name = user_arn.split('/')[-1] if '/user/' in user_arn else None
        
        print(f"   SUCCESS: Current identity: {user_arn}")
        print(f"   Account ID: {account_id}")
        print()
        
        if not user_name:
            print("   WARNING: Not an IAM user (might be a role). Skipping policy attachment.")
            print("   If you're using a role, ensure it has Bedrock permissions.")
            check_bedrock_access_only()
            return
        
        # Step 2: Check existing Bedrock permissions
        print("2. Checking existing Bedrock permissions...")
        iam = boto3.client('iam')
        
        has_bedrock_access = False
        try:
            response = iam.list_attached_user_policies(UserName=user_name)
            
            for policy in response.get('AttachedPolicies', []):
                if 'Bedrock' in policy['PolicyName']:
                    print(f"   SUCCESS: Found policy: {policy['PolicyName']}")
                    has_bedrock_access = True
        except ClientError as e:
            print(f"   WARNING: Could not list policies: {e}")
        
        print()
        
        # Step 3: Attach Bedrock permissions if missing
        if not has_bedrock_access:
            print("3. Attaching Bedrock permissions...")
            print("   Using: AmazonBedrockFullAccess (AWS managed policy)")
            
            try:
                iam.attach_user_policy(
                    UserName=user_name,
                    PolicyArn='arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
                )
                print("   SUCCESS: Attached AmazonBedrockFullAccess policy")
                print()
                print("   NOTE: Policy changes may take 1-2 minutes to propagate")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                print(f"   ERROR: Failed to attach policy: {error_code}")
                print(f"   Message: {e.response['Error']['Message']}")
                
                if error_code == 'AccessDenied':
                    print()
                    print("   ALTERNATIVE: Creating inline policy with minimum permissions")
                    
                    min_policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "bedrock:InvokeModel",
                                    "bedrock:InvokeModelWithResponseStream",
                                    "bedrock:ListFoundationModels"
                                ],
                                "Resource": "*"
                            }
                        ]
                    }
                    
                    try:
                        iam.put_user_policy(
                            UserName=user_name,
                            PolicyName='FileFerry-Bedrock-Access',
                            PolicyDocument=json.dumps(min_policy)
                        )
                        print("   SUCCESS: Created inline policy: FileFerry-Bedrock-Access")
                    except ClientError as e2:
                        print(f"   ERROR: Failed to create inline policy: {e2}")
                        print()
                        print("   MANUAL ACTION REQUIRED:")
                        print("   1. Go to AWS Console: IAM > Users")
                        print(f"   2. Select user: {user_name}")
                        print("   3. Attach policy: AmazonBedrockFullAccess")
        else:
            print("3. Bedrock access already configured (skipping attachment)")
        
        print()
        
        # Step 4: Verify Bedrock model access
        check_bedrock_access_only()
        
    except NoCredentialsError:
        print("ERROR: AWS credentials not configured.")
        print()
        print("SETUP REQUIRED:")
        print("1. Configure AWS credentials using one of these methods:")
        print()
        print("   Option A: Environment Variables")
        print("   ----------------------------------")
        print("   $env:AWS_ACCESS_KEY_ID = 'YOUR_ACCESS_KEY'")
        print("   $env:AWS_SECRET_ACCESS_KEY = 'YOUR_SECRET_KEY'")
        print("   $env:AWS_DEFAULT_REGION = 'us-east-1'")
        print()
        print("   Option B: AWS SSO (if your organization uses it)")
        print("   -------------------------------------------------")
        print("   1. Install AWS CLI: https://aws.amazon.com/cli/")
        print("   2. Run: aws configure sso")
        print("   3. Follow the prompts")
        print()
        print("   Option C: Shared Credentials File")
        print("   ----------------------------------")
        print("   1. Create file: %USERPROFILE%\\.aws\\credentials")
        print("   2. Add:")
        print("      [default]")
        print("      aws_access_key_id = YOUR_ACCESS_KEY")
        print("      aws_secret_access_key = YOUR_SECRET_KEY")
        print("      region = us-east-1")
        print()
    except ClientError as e:
        print(f"ERROR: {e}")
        print()
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        print()


def check_bedrock_access_only():
    """Check Bedrock model access without modifying IAM"""
    print("4. Verifying Bedrock model access...")
    
    model_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    region = "us-east-1"
    
    try:
        bedrock = boto3.client('bedrock', region_name=region)
        
        response = bedrock.list_foundation_models()
        print("   SUCCESS: Bedrock API access confirmed")
        
        # Check if our specific model is available
        our_model = None
        for model in response.get('modelSummaries', []):
            if model.get('modelId') == model_id:
                our_model = model
                break
        
        if our_model:
            print(f"   SUCCESS: Model available: {model_id}")
            status = our_model.get('modelLifecycle', {}).get('status', 'Unknown')
            print(f"   Model status: {status}")
            
            if status != 'ACTIVE':
                print()
                print(f"   WARNING: Model status is '{status}' (expected 'ACTIVE')")
                print("   ACTION REQUIRED: Enable model access in AWS Console")
        else:
            print(f"   WARNING: Model not found in available models")
            print("   ACTION REQUIRED: Request model access in AWS Console")
            print(f"   URL: https://console.aws.amazon.com/bedrock/home?region={region}#/modelaccess")
            print()
            print("   STEPS TO ENABLE MODEL ACCESS:")
            print("   1. Go to the URL above")
            print("   2. Click 'Manage model access' (top right)")
            print("   3. Find 'Anthropic' > 'Claude 3.5 Sonnet v2'")
            print("   4. Check the checkbox")
            print("   5. Click 'Request model access' (bottom)")
            print("   6. Wait 1-2 minutes for approval (usually instant)")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"   ERROR: Bedrock API access denied: {error_code}")
        print(f"   Message: {error_message}")
        print()
        print("   TROUBLESHOOTING STEPS:")
        print("   1. Check AWS region (must be us-east-1)")
        print("   2. Verify IAM policies are attached")
        print(f"   3. Request model access: https://console.aws.amazon.com/bedrock/home?region={region}#/modelaccess")
        
        if error_code == 'AccessDeniedException':
            print()
            print("   COMMON FIX:")
            print("   - Attach 'AmazonBedrockFullAccess' policy to your IAM user/role")
            print("   - Or create an inline policy with bedrock:InvokeModel permission")
            print()
            print("   IAM Policy Template (minimum permissions):")
            print("   {")
            print('     "Version": "2012-10-17",')
            print('     "Statement": [')
            print("       {")
            print('         "Effect": "Allow",')
            print('         "Action": [')
            print('           "bedrock:InvokeModel",')
            print('           "bedrock:InvokeModelWithResponseStream",')
            print('           "bedrock:ListFoundationModels"')
            print("         ],")
            print('         "Resource": "*"')
            print("       }")
            print("     ]")
            print("   }")
    
    print()


def print_summary():
    """Print final summary"""
    print("=" * 60)
    print("IAM Permission Check Complete")
    print("=" * 60)
    print()
    print("NEXT STEPS:")
    print("-----------")
    print()
    print("1. If model access was NOT enabled:")
    print("   a. Go to: https://console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess")
    print("   b. Click: 'Manage model access'")
    print("   c. Enable: Anthropic > Claude 3.5 Sonnet v2")
    print("   d. Click: 'Request model access'")
    print("   e. Wait 1-2 minutes")
    print()
    print("2. Clear Python cache:")
    print("   Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force")
    print()
    print("3. Test the FileFerry agent:")
    print("   python local_agent.py")
    print()
    print("4. If still failing, run this script again to verify:")
    print("   python fix_iam_bedrock_permissions.py")
    print()


if __name__ == '__main__':
    main()
    print_summary()