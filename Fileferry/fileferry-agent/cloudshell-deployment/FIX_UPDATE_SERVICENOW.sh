#!/bin/bash

# ============================================================================
# Fix FileFerry-UpdateServiceNow Lambda - Add requests library
# ============================================================================

set -e

echo "🔧 Fixing FileFerry-UpdateServiceNow Lambda..."
echo "Issue: Missing 'requests' library"
echo ""

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
FUNCTION_NAME="FileFerry-UpdateServiceNow"

echo "📦 Creating Lambda deployment package with requests library..."
echo ""

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd $TEMP_DIR

echo "Creating package directory..."
mkdir -p package

# Install requests library
echo "Installing requests library..."
pip3 install --target ./package requests

# Copy Lambda function code
echo "Copying Lambda function code..."
cat > package/update_servicenow.py << 'EOF'
"""
Lambda Function: Update ServiceNow
Updates ServiceNow tickets with transfer status
"""

import json
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, Any
import os


SERVICENOW_INSTANCE = os.environ.get('SERVICENOW_INSTANCE_URL', 'https://your-instance.service-now.com')
SERVICENOW_USERNAME = os.environ.get('SERVICENOW_USERNAME')
SERVICENOW_PASSWORD = os.environ.get('SERVICENOW_PASSWORD')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Update ServiceNow tickets with transfer completion
    
    Event structure:
    {
        "servicenow_tickets": ["INC0010001", "INC0010002"],
        "transfer_result": {
            "status": "completed",
            "bytes_transferred": 1024,
            "remote_path": "/uploads/file.txt"
        }
    }
    """
    
    try:
        tickets = event['servicenow_tickets']
        transfer_result = event.get('transfer_result', {})
        
        print(f"📝 Updating ServiceNow tickets: {tickets}")
        
        updates = []
        
        for ticket_number in tickets:
            # Get ticket sys_id
            sys_id = get_ticket_sys_id(ticket_number)
            
            if not sys_id:
                print(f"⚠️ Ticket not found: {ticket_number}")
                continue
            
            # Prepare update payload
            status = transfer_result.get('status', 'completed')
            
            if status == 'completed':
                work_notes = f"""Transfer Completed Successfully
                
Bytes Transferred: {transfer_result.get('bytes_transferred', 'N/A')}
Remote Path: {transfer_result.get('remote_path', 'N/A')}
MD5 Checksum: {transfer_result.get('md5_checksum', 'N/A')}
Completed At: {transfer_result.get('completed_at', 'N/A')}
"""
                state = "6"  # Resolved
            else:
                work_notes = f"""Transfer Failed
                
Error: {transfer_result.get('error', 'Unknown error')}
"""
                state = "4"  # Awaiting User Info / Failed
            
            # Update ticket
            url = f"{SERVICENOW_INSTANCE}/api/now/table/incident/{sys_id}"
            
            payload = {
                "state": state,
                "work_notes": work_notes,
                "close_notes": work_notes if status == 'completed' else None
            }
            
            response = requests.patch(
                url,
                json=payload,
                auth=HTTPBasicAuth(SERVICENOW_USERNAME, SERVICENOW_PASSWORD),
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✅ Updated ticket: {ticket_number}")
                updates.append({
                    'ticket': ticket_number,
                    'status': 'updated'
                })
            else:
                print(f"❌ Failed to update ticket: {ticket_number} - {response.text}")
                updates.append({
                    'ticket': ticket_number,
                    'status': 'failed',
                    'error': response.text
                })
        
        return {
            'status': 'completed',
            'tickets_updated': len([u for u in updates if u['status'] == 'updated']),
            'updates': updates
        }
        
    except Exception as e:
        print(f"❌ ServiceNow update error: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


def get_ticket_sys_id(ticket_number: str) -> str:
    """Get sys_id from ticket number"""
    try:
        url = f"{SERVICENOW_INSTANCE}/api/now/table/incident"
        params = {
            'sysparm_query': f'number={ticket_number}',
            'sysparm_fields': 'sys_id',
            'sysparm_limit': 1
        }
        
        response = requests.get(
            url,
            params=params,
            auth=HTTPBasicAuth(SERVICENOW_USERNAME, SERVICENOW_PASSWORD),
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('result') and len(result['result']) > 0:
                return result['result'][0]['sys_id']
        
        return None
        
    except Exception as e:
        print(f"❌ Error getting sys_id for {ticket_number}: {str(e)}")
        return None
EOF

# Create deployment package
echo "Creating deployment package..."
cd package
zip -r ../lambda-package.zip . > /dev/null
cd ..

echo "✅ Deployment package created: $(du -h lambda-package.zip | cut -f1)"
echo ""

# Update Lambda function
echo "📤 Updating Lambda function..."
aws lambda update-function-code \
  --function-name $FUNCTION_NAME \
  --zip-file fileb://lambda-package.zip \
  --region $REGION

echo "✅ Lambda function updated!"
echo ""

# Wait for update to complete
echo "⏳ Waiting for Lambda update to complete..."
aws lambda wait function-updated \
  --function-name $FUNCTION_NAME \
  --region $REGION

echo "✅ Lambda update complete!"
echo ""

# Cleanup
cd /
rm -rf $TEMP_DIR

echo "=========================================="
echo "🎉 Fix Applied Successfully!"
echo "=========================================="
echo ""
echo "Lambda Function: $FUNCTION_NAME"
echo "Region: $REGION"
echo ""
echo "✅ 'requests' library added"
echo "✅ Function code updated"
echo ""
echo "Next Step:"
echo "  Test the Lambda function in AWS Console"
echo ""
echo "Test Event JSON:"
echo '{'
echo '  "servicenow_tickets": ["INC0010001", "INC0010002"],'
echo '  "transfer_result": {'
echo '    "status": "completed",'
echo '    "bytes_transferred": 1048576,'
echo '    "remote_path": "/uploads/test.txt"'
echo '  }'
echo '}'
echo ""
