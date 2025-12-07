"""Check Lambda function configuration"""
import boto3

client = boto3.client('lambda', region_name='us-east-1')
config = client.get_function_configuration(FunctionName='FileFerry-CreateServiceNowTickets')

print("\n" + "=" * 60)
print("📋 LAMBDA FUNCTION CONFIGURATION")
print("=" * 60)
print(f"\nFunction Name: {config['FunctionName']}")
print(f"Handler: {config['Handler']}")
print(f"Runtime: {config['Runtime']}")
print(f"CodeSize: {config['CodeSize']} bytes")
print(f"Timeout: {config['Timeout']} seconds")
print(f"Memory: {config['MemorySize']} MB")
print(f"Last Modified: {config['LastModified']}")

if 'Layers' in config:
    print(f"\nLayers:")
    for layer in config['Layers']:
        print(f"  • {layer['Arn']}")

if 'Environment' in config and 'Variables' in config['Environment']:
    print(f"\nEnvironment Variables:")
    for key, value in config['Environment']['Variables'].items():
        if 'PASSWORD' in key.upper():
            value = '***SET***'
        print(f"  • {key}: {value}")

print("\n" + "=" * 60)
print("\n🔍 ISSUE ANALYSIS:")
print("=" * 60)

# The handler should be lambda_function.lambda_handler
# because the deploy script renames create_servicenow_tickets.py to lambda_function.py
if config['Handler'] == 'lambda_function.lambda_handler':
    print("✅ Handler is correctly configured: lambda_function.lambda_handler")
else:
    print(f"⚠️  Handler is: {config['Handler']}")
    print("   Expected: lambda_function.lambda_handler")
    print("\n   The deployment script copies create_servicenow_tickets.py")
    print("   to lambda_function.py, so handler should match.")

# Check if the error might be something else
print("\n💡 POSSIBLE CAUSES OF ImportModuleError:")
print("   1. Deployment package structure is wrong")
print("   2. File was not properly renamed during deployment")
print("   3. Lambda layer conflict")
print("   4. Code was not actually deployed")
print("\n" + "=" * 60)
