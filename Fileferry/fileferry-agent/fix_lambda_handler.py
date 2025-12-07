"""
Fix Lambda Handler Issue
Updates FileFerry-CreateServiceNowTickets Lambda with correct code
"""

import boto3
import zipfile
import io
import os

def fix_lambda_handler():
    """Fix the Lambda function by redeploying with correct handler"""
    
    print("\n🔧 FIXING LAMBDA HANDLER ISSUE\n")
    print("=" * 60)
    
    # Configuration
    function_name = 'FileFerry-CreateServiceNowTickets'
    region = 'us-east-1'
    source_file = 'cloudshell-deployment/lambda_functions/create_servicenow_tickets.py'
    
    # Check if source file exists
    if not os.path.exists(source_file):
        print(f"❌ ERROR: Source file not found: {source_file}")
        return False
    
    print(f"✅ Source file found: {source_file}")
    
    # Create Lambda client
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        # Read the source code with UTF-8 encoding
        with open(source_file, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        print(f"✅ Code loaded ({len(code_content)} bytes)")
        
        # Create deployment package in memory
        print("\n📦 Creating deployment package...")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add the code as lambda_function.py (AWS expects this name)
            zip_file.writestr('lambda_function.py', code_content)
        
        zip_buffer.seek(0)
        zip_bytes = zip_buffer.read()
        
        print(f"✅ Package created ({len(zip_bytes)} bytes)")
        
        # Update Lambda function code
        print(f"\n🚀 Updating Lambda function: {function_name}...")
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_bytes
        )
        
        print(f"✅ Code updated successfully!")
        print(f"   Version: {response['Version']}")
        print(f"   Last Modified: {response['LastModified']}")
        print(f"   Code Size: {response['CodeSize']} bytes")
        
        # Verify the handler configuration
        print("\n🔍 Verifying handler configuration...")
        config = lambda_client.get_function_configuration(FunctionName=function_name)
        
        print(f"✅ Handler: {config['Handler']}")
        print(f"   Runtime: {config['Runtime']}")
        print(f"   Timeout: {config['Timeout']} seconds")
        print(f"   Memory: {config['MemorySize']} MB")
        
        if config['Handler'] != 'lambda_function.lambda_handler':
            print(f"\n⚠️  WARNING: Handler is '{config['Handler']}'")
            print("   Updating handler to 'lambda_function.lambda_handler'...")
            
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Handler='lambda_function.lambda_handler'
            )
            print("✅ Handler updated!")
        
        # Check layers
        if 'Layers' in config:
            print(f"\n📚 Lambda Layers:")
            for layer in config['Layers']:
                layer_name = layer['Arn'].split(':')[-2]
                print(f"   • {layer_name}")
        
        # Check environment variables
        if 'Environment' in config and 'Variables' in config['Environment']:
            env_vars = config['Environment']['Variables']
            print(f"\n🔐 Environment Variables:")
            for key in ['SERVICENOW_INSTANCE_URL', 'SERVICENOW_USERNAME']:
                if key in env_vars:
                    value = env_vars[key]
                    if 'PASSWORD' in key:
                        value = '***SET***'
                    print(f"   • {key}: {value}")
        
        print("\n" + "=" * 60)
        print("✅ LAMBDA FUNCTION FIXED SUCCESSFULLY!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = fix_lambda_handler()
    
    if success:
        print("\n🎯 NEXT STEP: Re-run integration test")
        print("\nRun this command:")
        print("  python test_integration.py")
        print("\nExpected result:")
        print("  ✅ Lambda invocation: SUCCESS")
        print("  ✅ No ImportModuleError")
        print("  ✅ ServiceNow tickets created")
    else:
        print("\n❌ Fix failed - please check errors above")
