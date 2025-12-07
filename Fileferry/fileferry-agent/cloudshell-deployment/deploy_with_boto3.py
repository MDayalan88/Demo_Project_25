#!/usr/bin/env python3
"""
Deploy FileFerry Lambda functions using boto3 (no CLI installation needed)
Run in CloudShell: python3 deploy_with_boto3.py
"""

import boto3
import json
import zipfile
import io
import time
from pathlib import Path

# Configuration
REGION = 'us-east-1'
ACCOUNT_ID = '637423332185'
LAMBDA_ROLE_ARN = f'arn:aws:iam::{ACCOUNT_ID}:role/FileFerryLambdaExecutionRole'
STEP_FUNCTIONS_ROLE_ARN = f'arn:aws:iam::{ACCOUNT_ID}:role/FileFerryStepFunctionsRole'

# Initialize AWS clients
lambda_client = boto3.client('lambda', region_name=REGION)
sfn_client = boto3.client('stepfunctions', region_name=REGION)

# Lambda functions configuration
LAMBDA_FUNCTIONS = [
    {'name': 'FileFerry-ValidateInput', 'handler': 'validate_input.lambda_handler', 'file': 'validate_input.py'},
    {'name': 'FileFerry-AuthSSO', 'handler': 'auth_sso.lambda_handler', 'file': 'auth_sso.py'},
    {'name': 'FileFerry-DownloadS3', 'handler': 'download_s3.lambda_handler', 'file': 'download_s3.py'},
    {'name': 'FileFerry-TransferFTP', 'handler': 'transfer_ftp.lambda_handler', 'file': 'transfer_ftp.py'},
    {'name': 'FileFerry-ChunkedTransfer', 'handler': 'chunked_transfer.lambda_handler', 'file': 'chunked_transfer.py'},
    {'name': 'FileFerry-UpdateServiceNow', 'handler': 'update_servicenow.lambda_handler', 'file': 'update_servicenow.py'},
    {'name': 'FileFerry-NotifyUser', 'handler': 'notify_user.lambda_handler', 'file': 'notify_user.py'},
    {'name': 'FileFerry-Cleanup', 'handler': 'cleanup.lambda_handler', 'file': 'cleanup.py'},
]

def create_zip_bytes(python_file):
    """Create ZIP file in memory"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(python_file, Path(python_file).name)
    zip_buffer.seek(0)
    return zip_buffer.read()

def deploy_lambda(func_config):
    """Deploy or update a Lambda function"""
    func_name = func_config['name']
    
    # Check if function exists
    try:
        lambda_client.get_function(FunctionName=func_name)
        exists = True
        print(f"✓ {func_name} already exists - skipping")
        return True
    except lambda_client.exceptions.ResourceNotFoundException:
        exists = False
    
    print(f"⏳ Deploying {func_name}...", end='', flush=True)
    
    try:
        # Create ZIP from Python file
        zip_data = create_zip_bytes(func_config['file'])
        
        if not exists:
            # Create new function
            response = lambda_client.create_function(
                FunctionName=func_name,
                Runtime='python3.11',
                Role=LAMBDA_ROLE_ARN,
                Handler=func_config['handler'],
                Code={'ZipFile': zip_data},
                Timeout=300,
                MemorySize=512,
                Environment={
                    'Variables': {
                        'DYNAMODB_TABLE': 'FileFerry-Transfers',
                        'REGION': REGION
                    }
                }
            )
            print(f" ✅ Created")
        else:
            # Update existing function
            response = lambda_client.update_function_code(
                FunctionName=func_name,
                ZipFile=zip_data
            )
            print(f" ✅ Updated")
        
        return True
    except Exception as e:
        print(f" ❌ Failed: {str(e)}")
        return False

def deploy_step_functions():
    """Deploy Step Functions state machine"""
    state_machine_name = 'FileFerry-TransferStateMachine'
    
    print(f"\n⏳ Deploying Step Functions state machine...", flush=True)
    
    try:
        # Read state machine definition
        with open('step_functions_state_machine.json', 'r') as f:
            definition = f.read()
        
        # Check if state machine exists
        try:
            response = sfn_client.describe_state_machine(
                stateMachineArn=f'arn:aws:states:{REGION}:{ACCOUNT_ID}:stateMachine:{state_machine_name}'
            )
            exists = True
        except sfn_client.exceptions.StateMachineDoesNotExist:
            exists = False
        
        if not exists:
            # Create state machine
            response = sfn_client.create_state_machine(
                name=state_machine_name,
                definition=definition,
                roleArn=STEP_FUNCTIONS_ROLE_ARN
            )
            state_machine_arn = response['stateMachineArn']
            print(f"✅ State machine created")
        else:
            # Update state machine
            state_machine_arn = f'arn:aws:states:{REGION}:{ACCOUNT_ID}:stateMachine:{state_machine_name}'
            response = sfn_client.update_state_machine(
                stateMachineArn=state_machine_arn,
                definition=definition
            )
            print(f"✅ State machine updated")
        
        print(f"\n🎯 State Machine ARN:")
        print(f"   {state_machine_arn}")
        return state_machine_arn
    
    except FileNotFoundError:
        print(f"❌ step_functions_state_machine.json not found")
        return None
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return None

def verify_deployment():
    """Verify all functions are deployed"""
    print(f"\n🔍 Verifying deployment...")
    
    deployed = []
    missing = []
    
    for func_config in LAMBDA_FUNCTIONS:
        try:
            lambda_client.get_function(FunctionName=func_config['name'])
            deployed.append(func_config['name'])
        except lambda_client.exceptions.ResourceNotFoundException:
            missing.append(func_config['name'])
    
    print(f"\n✅ Deployed: {len(deployed)}/{len(LAMBDA_FUNCTIONS)}")
    for name in deployed:
        print(f"   ✓ {name}")
    
    if missing:
        print(f"\n❌ Missing: {len(missing)}")
        for name in missing:
            print(f"   ✗ {name}")
    
    return len(missing) == 0

def main():
    print("=" * 60)
    print("FileFerry Lambda Deployment - boto3")
    print("=" * 60)
    print(f"Region: {REGION}")
    print(f"Account: {ACCOUNT_ID}")
    print(f"Functions: {len(LAMBDA_FUNCTIONS)}")
    print("=" * 60)
    
    # Deploy Lambda functions
    print("\n📦 Deploying Lambda functions...")
    success_count = 0
    for func_config in LAMBDA_FUNCTIONS:
        if deploy_lambda(func_config):
            success_count += 1
        time.sleep(1)  # Rate limiting
    
    print(f"\n✅ Deployed {success_count}/{len(LAMBDA_FUNCTIONS)} functions")
    
    # Deploy Step Functions
    state_machine_arn = deploy_step_functions()
    
    # Verify deployment
    all_deployed = verify_deployment()
    
    # Summary
    print("\n" + "=" * 60)
    if all_deployed and state_machine_arn:
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("=" * 60)
        print(f"\n📋 Next steps:")
        print(f"1. Copy this ARN to config/config.yaml:")
        print(f"   {state_machine_arn}")
        print(f"2. Test the workflow")
    else:
        print("⚠️  DEPLOYMENT INCOMPLETE")
        print("=" * 60)
        print("Run the script again to retry failed deployments")
    
    print("\n")

if __name__ == '__main__':
    main()
