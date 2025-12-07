"""
FileFerry Component Tests
Validates all components and AWS connectivity
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("\n" + "="*70)
print("🧪 FileFerry Agent - Component Test Suite")
print("="*70)

# Test 1: Python environment
print("\n✅ Test 1: Python Environment")
print(f"   Version: {sys.version.split()[0]}")
print(f"   Path: {sys.executable}")

# Test 2: Required packages
print("\n✅ Test 2: Required Packages")
packages = {
    'boto3': 'AWS SDK',
    'yaml': 'YAML Parser',
    'aiohttp': 'Async HTTP',
    'aws_xray_sdk': 'AWS X-Ray'
}

for package, description in packages.items():
    try:
        __import__(package.replace('-', '_'))
        print(f"   ✅ {package:20s} - {description}")
    except ImportError:
        print(f"   ❌ {package:20s} - NOT INSTALLED")

# Test 3: AWS credentials
print("\n✅ Test 3: AWS Credentials")
try:
    import boto3
    sts = boto3.client('sts')
    identity = sts.get_caller_identity()
    print(f"   ✅ Valid credentials")
    print(f"   Account: {identity['Account']}")
    print(f"   Region: {boto3.Session().region_name or 'us-east-1'}")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# Test 4: File structure
print("\n✅ Test 4: Project Structure")
files = [
    'src/ai_agent/bedrock_agent.py',
    'src/ai_agent/agent_tools.py',
    'src/teams_bot/adaptive_cards.py',
    'config/config.yaml',
    'infrastructure/create_dynamodb_tables.py'
]

for file in files:
    exists = os.path.exists(file)
    status = "✅" if exists else "❌"
    print(f"   {status} {file}")

print("\n" + "="*70)
print("📊 Test Complete!")
print("="*70 + "\n")