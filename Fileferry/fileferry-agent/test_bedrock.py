"""
Test AWS Bedrock Model Invocation
Updated for inference profile requirement (Dec 2024)
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError


def test_bedrock_invocation():
    """
    Test Bedrock model invocation using inference profile
    Model will auto-enable on first call
    """
    
    print("\n" + "="*70)
    print("🧪 Testing AWS Bedrock Model Invocation")
    print("="*70)
    print("\n💡 Note: Using inference profile for Claude 3.5 Sonnet v2")
    print("   First call may take 2-3 seconds (one-time setup)")
    print("="*70 + "\n")
    
    try:
        # Create Bedrock Runtime client
        print("🔧 Initializing Bedrock Runtime client...")
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        print("   ✅ Client initialized\n")
        
        # Try multiple model identifiers (in order of preference)
        model_ids = [
            # Inference profiles (recommended)
            'us.anthropic.claude-3-5-sonnet-20241022-v2:0',
            'anthropic.claude-3-5-sonnet-20241022-v2:0',
            # Fallback to v1
            'us.anthropic.claude-3-5-sonnet-20240620-v1:0',
            'anthropic.claude-3-5-sonnet-20240620-v1:0',
            # Cross-region inference profile
            'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0'
        ]
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": "Say 'FileFerry agent is working!' in exactly one sentence."
                }
            ]
        }
        
        success = False
        last_error = None
        
        for model_id in model_ids:
            try:
                print(f"🤖 Attempting to invoke Claude 3.5 Sonnet...")
                print(f"   Model ID: {model_id}")
                print(f"   Region: us-east-1\n")
                
                # Invoke model (auto-enables if needed)
                response = bedrock_runtime.invoke_model(
                    modelId=model_id,
                    body=json.dumps(request_body)
                )
                
                # Parse response
                response_body = json.loads(response['body'].read())
                ai_response = response_body['content'][0]['text']
                
                print("="*70)
                print("✅ SUCCESS! Bedrock Model Invocation Working")
                print("="*70)
                print(f"\n🤖 AI Response:")
                print(f"   {ai_response}\n")
                
                print("="*70)
                print("📊 Response Metadata")
                print("="*70)
                print(f"   Model ID Used: {model_id}")
                print(f"   Model: {response_body.get('model', 'N/A')}")
                print(f"   Stop Reason: {response_body.get('stop_reason', 'N/A')}")
                print(f"   Input Tokens: {response_body.get('usage', {}).get('input_tokens', 0)}")
                print(f"   Output Tokens: {response_body.get('usage', {}).get('output_tokens', 0)}")
                
                print("\n" + "="*70)
                print("🎉 Bedrock is Ready for FileFerry!")
                print("="*70)
                
                print("\n📋 Working Model ID for your config:")
                print(f"   {model_id}")
                
                print("\n📋 Next Steps:")
                print("   1. Update config/config.yaml with working model ID")
                print("   2. Test FileFerry agent locally:")
                print("      python test_agent.py")
                print("   3. Deploy to Lambda:")
                print("      python infrastructure/deploy_lambda.py")
                print("\n")
                
                success = True
                break
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                last_error = e
                print(f"   ⚠️  Model ID failed: {error_code}")
                print(f"   Trying next option...\n")
                continue
        
        if not success:
            raise last_error
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        
        print("\n" + "="*70)
        print(f"❌ Error: {error_code}")
        print("="*70)
        print(f"\n{error_msg}\n")
        
        if error_code == 'ValidationException':
            if 'inference profile' in error_msg.lower():
                print("💡 Issue: Model requires inference profile")
                print("\n   AWS Bedrock now requires inference profiles for Claude models.")
                print("   The script tried multiple formats but none worked.")
                print("\n   Manual fix:")
                print("   1. Go to AWS Console → Bedrock → Model catalog")
                print("   2. Find: Claude 3.5 Sonnet v2")
                print("   3. Copy the correct inference profile ID")
                print("   4. Update test_bedrock_invoke.py with that ID")
                print("\n   Common formats:")
                print("   • us.anthropic.claude-3-5-sonnet-20241022-v2:0")
                print("   • anthropic.claude-3-5-sonnet-20241022-v2:0")
                print("   • arn:aws:bedrock:us-east-1::foundation-model/...")
            else:
                print("💡 Possible Causes:")
                print("   1. Model not available in us-east-1")
                print("   2. Try us-west-2 region instead")
                print("   3. Request format incorrect")
        
        elif error_code == 'AccessDeniedException':
            if 'not enabled' in error_msg.lower() or 'use case' in error_msg.lower():
                print("💡 Action Required:")
                print("   Some first-time users need to submit use case details")
                print("\n   Steps:")
                print("   1. Go to: https://console.aws.amazon.com/bedrock")
                print("   2. Navigate to: Model catalog → Anthropic Claude")
                print("   3. Click on: Claude 3.5 Sonnet v2")
                print("   4. If prompted, fill out use case form")
                print("   5. Submit and wait for approval (usually instant)")
                print("\n   Then retry: python test_bedrock_invoke.py")
            else:
                print("💡 Cause: Missing IAM permission")
                print("\n   Fix: Add bedrock:InvokeModel permission")
                print("   See previous instructions for adding Bedrock IAM policy")
        
        elif error_code == 'ResourceNotFoundException':
            print("💡 Cause: Model not found")
            print("\n   Try different region:")
            print("   • us-west-2")
            print("   • eu-west-1")
            print("   • ap-southeast-1")
        
        elif error_code == 'ThrottlingException':
            print("💡 Cause: Rate limit exceeded")
            print("   Wait a few seconds and retry")
        
        else:
            print("💡 Troubleshooting:")
            print("   1. Verify IAM permissions: python check_bedrock_permissions.py")
            print("   2. Check AWS credentials are correct")
            print("   3. Try different region (us-west-2)")
        
        print("\n")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("   1. Check AWS credentials configuration")
        print("   2. Verify internet connectivity")
        print("   3. Check boto3 version: pip show boto3")
        print("\n")
        return False


def list_available_models():
    """List available Bedrock models in the region"""
    print("\n" + "="*70)
    print("📋 Listing Available Bedrock Models")
    print("="*70 + "\n")
    
    try:
        bedrock = boto3.client('bedrock', region_name='us-east-1')
        
        response = bedrock.list_foundation_models()
        models = response.get('modelSummaries', [])
        
        claude_models = [m for m in models if 'claude' in m['modelId'].lower()]
        
        print(f"✅ Found {len(claude_models)} Claude models:\n")
        
        for model in claude_models:
            print(f"   Model: {model['modelName']}")
            print(f"   ID: {model['modelId']}")
            print(f"   Provider: {model['providerName']}")
            status = model.get('modelLifecycle', {}).get('status', 'UNKNOWN')
            print(f"   Status: {status}")
            
            # Check for inference profile info
            if 'inferenceTypesSupported' in model:
                print(f"   Inference Types: {', '.join(model['inferenceTypesSupported'])}")
            
            print()
        
        return claude_models
        
    except ClientError as e:
        print(f"❌ Cannot list models: {e.response['Error']['Code']}")
        print("   This is OK - continue with test")
        return []
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return []


if __name__ == "__main__":
    # First, try to list available models
    available_models = list_available_models()
    
    # Then test invocation
    success = test_bedrock_invocation()
    
    sys.exit(0 if success else 1)