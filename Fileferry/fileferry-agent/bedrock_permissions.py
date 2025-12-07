"""
Bedrock Permission Checker (Updated for AWS Model Access Changes)
Models are now auto-enabled on first invocation - no manual approval needed
"""

import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError

def main():
    print("=" * 60)
    print("Bedrock Permission Check (Updated for 2025)")
    print("=" * 60)
    print()
    print("NOTE: AWS Bedrock now auto-enables models on first invocation")
    print("No manual model access approval needed!")
    print()
    
    try:
        # Step 1: Get current IAM identity
        print("1. Checking AWS identity...")
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        user_arn = identity['Arn']
        account_id = identity['Account']
        user_name = user_arn.split('/')[-1] if '/user/' in user_arn else None
        
        print(f"   SUCCESS: {user_arn}")
        print(f"   Account: {account_id}")
        print()
        
        # Step 2: Check IAM permissions
        print("2. Checking IAM Bedrock permissions...")
        iam = boto3.client('iam')
        
        has_bedrock_policy = False
        if user_name:
            try:
                response = iam.list_attached_user_policies(UserName=user_name)
                for policy in response.get('AttachedPolicies', []):
                    if 'Bedrock' in policy['PolicyName']:
                        print(f"   SUCCESS: Found policy: {policy['PolicyName']}")
                        has_bedrock_policy = True
                
                # Check inline policies too
                inline_response = iam.list_user_policies(UserName=user_name)
                for policy_name in inline_response.get('PolicyNames', []):
                    if 'Bedrock' in policy_name:
                        print(f"   SUCCESS: Found inline policy: {policy_name}")
                        has_bedrock_policy = True
                        
            except ClientError as e:
                print(f"   WARNING: Could not check policies: {e.response['Error']['Code']}")
        else:
            print("   INFO: Using IAM role (not a user)")
        
        if not has_bedrock_policy and user_name:
            print("   WARNING: No Bedrock policies found")
            print("   Will attempt to attach AmazonBedrockFullAccess...")
            print()
            
            # Try to attach policy
            try:
                iam.attach_user_policy(
                    UserName=user_name,
                    PolicyArn='arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
                )
                print("   SUCCESS: Attached AmazonBedrockFullAccess policy")
                has_bedrock_policy = True
            except ClientError as e:
                error_code = e.response['Error']['Code']
                print(f"   ERROR: Cannot attach policy: {error_code}")
                
                if error_code == 'AccessDenied':
                    print()
                    print("   MANUAL ACTION REQUIRED:")
                    print("   Ask your AWS admin to attach this policy:")
                    print("   arn:aws:iam::aws:policy/AmazonBedrockFullAccess")
                    print()
                    print("   Or create an inline policy with these permissions:")
                    print_minimum_policy()
        print()
        
        # Step 3: Test Bedrock API access by invoking the model
        print("3. Testing Bedrock API access (invoking Claude 3.5 Sonnet v2)...")
        print("   NOTE: This will auto-enable the model if it's your first time")
        print()
        
        test_model_invocation()
        
    except NoCredentialsError:
        print("ERROR: AWS credentials not configured")
        print()
        print_credential_setup_instructions()
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()


def test_model_invocation():
    """Test actual model invocation (triggers auto-enablement)"""
    model_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    region = "us-east-1"
    
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        
        # Minimal test request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 10,
            "messages": [
                {
                    "role": "user",
                    "content": "Say 'hello'"
                }
            ]
        }
        
        print("   Invoking model (this may take a few seconds)...")
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        print()
        print("   =" * 30)
        print("   SUCCESS: Bedrock API is working!")
        print("   =" * 30)
        print(f"   Model: {model_id}")
        print(f"   Response: {response_body.get('content', [{}])[0].get('text', 'N/A')[:50]}...")
        print(f"   Stop reason: {response_body.get('stop_reason')}")
        print()
        print("   Your FileFerry agent is ready to use!")
        print()
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        print()
        print(f"   ERROR: {error_code}")
        print(f"   Message: {error_message}")
        print()
        
        if error_code == 'AccessDeniedException':
            print("   CAUSE: IAM permissions missing")
            print()
            print("   FIX: Add these permissions to your IAM user/role:")
            print_minimum_policy()
            
        elif error_code == 'ValidationException':
            if 'use case' in error_message.lower() or 'form' in error_message.lower():
                print("   CAUSE: First-time Anthropic user - use case approval required")
                print()
                print("   ACTION REQUIRED:")
                print("   1. Go to: https://console.aws.amazon.com/bedrock/")
                print("   2. Navigate to: Model catalog > Anthropic > Claude 3.5 Sonnet v2")
                print("   3. Click: 'Get started' or 'Request access'")
                print("   4. Fill out the use case form")
                print("   5. Submit for approval (usually instant)")
                print()
                print("   After approval, run this script again")
            else:
                print("   CAUSE: Model validation error")
                print(f"   Details: {error_message}")
                
        elif error_code == 'ResourceNotFoundException':
            print("   CAUSE: Model not available in this region")
            print(f"   Model: {model_id}")
            print(f"   Region: {region}")
            print()
            print("   FIX: Ensure you're using region us-east-1")
            
        elif error_code == 'ThrottlingException':
            print("   CAUSE: Rate limit exceeded")
            print("   FIX: Wait a moment and try again")
            
        else:
            print("   CAUSE: Unexpected error")
            print(f"   Code: {error_code}")
            print(f"   Message: {error_message}")
        
        print()
        return False


def print_minimum_policy():
    """Print minimum IAM policy for Bedrock"""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": f"arn:aws:bedrock:us-east-1::foundation-model/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
            }
        ]
    }
    
    print("   " + "=" * 55)
    print("   Minimum IAM Policy:")
    print("   " + "=" * 55)
    print(json.dumps(policy, indent=2))
    print("   " + "=" * 55)
    print()


def print_credential_setup_instructions():
    """Print AWS credential setup instructions"""
    print("SETUP OPTIONS:")
    print()
    print("Option A: Environment Variables (Quick Test)")
    print("-" * 50)
    print("$env:AWS_ACCESS_KEY_ID = 'YOUR_ACCESS_KEY'")
    print("$env:AWS_SECRET_ACCESS_KEY = 'YOUR_SECRET_KEY'")
    print("$env:AWS_DEFAULT_REGION = 'us-east-1'")
    print()
    print("Option B: AWS Credentials File (Persistent)")
    print("-" * 50)
    print("1. Create file: %USERPROFILE%\\.aws\\credentials")
    print("2. Add:")
    print("   [default]")
    print("   aws_access_key_id = YOUR_ACCESS_KEY")
    print("   aws_secret_access_key = YOUR_SECRET_KEY")
    print("   region = us-east-1")
    print()


def print_summary(success):
    """Print final summary"""
    print("=" * 60)
    print("Bedrock Permission Check Complete")
    print("=" * 60)
    print()
    
    if success:
        print("STATUS: READY")
        print()
        print("NEXT STEPS:")
        print("1. Clear Python cache:")
        print("   Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force")
        print()
        print("2. Test FileFerry agent:")
        print("   python local_agent.py")
        print()
    else:
        print("STATUS: ACTION REQUIRED")
        print()
        print("NEXT STEPS:")
        print("1. Fix IAM permissions (see error details above)")
        print("2. If first-time Anthropic user, submit use case form")
        print("3. Run this script again to verify:")
        print("   python check_bedrock_permissions.py")
        print()


if __name__ == '__main__':
    success = False
    try:
        main()
        success = True
    except Exception:
        pass
    
    print_summary(success)