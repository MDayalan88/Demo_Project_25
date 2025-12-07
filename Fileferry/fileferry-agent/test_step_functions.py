#!/usr/bin/env python3
"""
Test FileFerry Step Functions End-to-End Transfer
Tests the complete workflow: Validate → Auth → Download → Transfer → Update → Notify → Cleanup
"""

import boto3
import json
import time
from datetime import datetime

# Configuration
REGION = 'us-east-1'
STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:637423332185:stateMachine:FileFerry-TransferStateMachine'

# Initialize client
sfn_client = boto3.client('stepfunctions', region_name=REGION)

# Test payload
test_input = {
    "transfer_id": f"test-{int(time.time())}",
    "user_id": "test-user@example.com",
    "request_type": "file_transfer",
    "source": {
        "type": "s3",
        "bucket": "fileferry-test-bucket",
        "key": "test-files/sample.txt",
        "region": "us-east-1"
    },
    "destination": {
        "type": "ftp",
        "host": "ftp.example.com",
        "port": 21,
        "username": "ftpuser",
        "path": "/uploads/sample.txt",
        "protocol": "ftp"
    },
    "options": {
        "enable_compression": False,
        "verify_checksum": True,
        "chunk_size": 10485760
    },
    "servicenow": {
        "ticket_number": "INC0010002",
        "update_frequency": "on_completion"
    },
    "notification": {
        "email": "test-user@example.com",
        "send_on_completion": True
    }
}

def start_execution():
    """Start Step Functions execution"""
    print("=" * 70)
    print("FileFerry Step Functions - End-to-End Test")
    print("=" * 70)
    print(f"\nState Machine: {STATE_MACHINE_ARN}")
    print(f"Transfer ID: {test_input['transfer_id']}")
    print(f"Source: s3://{test_input['source']['bucket']}/{test_input['source']['key']}")
    print(f"Destination: {test_input['destination']['type']}://{test_input['destination']['host']}{test_input['destination']['path']}")
    print("\n" + "-" * 70)
    
    try:
        # Start execution
        print("\n⏳ Starting Step Functions execution...")
        response = sfn_client.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=test_input['transfer_id'],
            input=json.dumps(test_input)
        )
        
        execution_arn = response['executionArn']
        print(f"✅ Execution started!")
        print(f"   ARN: {execution_arn}")
        print(f"   Started: {response['startDate']}")
        
        return execution_arn
    
    except sfn_client.exceptions.ExecutionAlreadyExists:
        print("⚠️  Execution with this name already exists")
        execution_arn = f"{STATE_MACHINE_ARN.replace(':stateMachine:', ':execution:')}:{test_input['transfer_id']}"
        return execution_arn
    
    except Exception as e:
        print(f"❌ Failed to start execution: {str(e)}")
        return None

def monitor_execution(execution_arn):
    """Monitor execution status"""
    print("\n" + "-" * 70)
    print("📊 Monitoring execution status...\n")
    
    last_status = None
    start_time = time.time()
    
    while True:
        try:
            response = sfn_client.describe_execution(executionArn=execution_arn)
            status = response['status']
            
            if status != last_status:
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed}s] Status: {status}")
                last_status = status
            
            if status in ['SUCCEEDED', 'FAILED', 'TIMED_OUT', 'ABORTED']:
                print("\n" + "-" * 70)
                print(f"🏁 Execution {status}")
                print("-" * 70)
                
                if status == 'SUCCEEDED':
                    print("\n✅ Transfer completed successfully!")
                    if 'output' in response:
                        output = json.loads(response['output'])
                        print("\nOutput:")
                        print(json.dumps(output, indent=2))
                
                elif status == 'FAILED':
                    print("\n❌ Transfer failed!")
                    if 'error' in response:
                        print(f"Error: {response['error']}")
                    if 'cause' in response:
                        print(f"Cause: {response['cause']}")
                
                print(f"\nExecution time: {int(time.time() - start_time)}s")
                break
            
            time.sleep(2)
        
        except Exception as e:
            print(f"❌ Error monitoring execution: {str(e)}")
            break

def get_execution_history(execution_arn):
    """Get detailed execution history"""
    print("\n" + "=" * 70)
    print("📜 Execution History")
    print("=" * 70)
    
    try:
        response = sfn_client.get_execution_history(
            executionArn=execution_arn,
            maxResults=50,
            reverseOrder=False
        )
        
        events = response['events']
        print(f"\nTotal events: {len(events)}\n")
        
        for event in events:
            event_type = event['type']
            timestamp = event['timestamp'].strftime('%H:%M:%S')
            
            if 'TaskStateEntered' in event_type:
                state_name = event['stateEnteredEventDetails']['name']
                print(f"[{timestamp}] ▶️  Entered: {state_name}")
            
            elif 'TaskStateExited' in event_type:
                state_name = event['stateExitedEventDetails']['name']
                print(f"[{timestamp}] ✅ Completed: {state_name}")
            
            elif 'TaskFailed' in event_type:
                print(f"[{timestamp}] ❌ Task Failed")
                if 'taskFailedEventDetails' in event:
                    details = event['taskFailedEventDetails']
                    print(f"           Error: {details.get('error', 'Unknown')}")
                    print(f"           Cause: {details.get('cause', 'Unknown')}")
            
            elif 'ExecutionSucceeded' in event_type:
                print(f"[{timestamp}] 🎉 Execution Succeeded")
            
            elif 'ExecutionFailed' in event_type:
                print(f"[{timestamp}] 💥 Execution Failed")
    
    except Exception as e:
        print(f"❌ Error getting history: {str(e)}")

def main():
    # Start execution
    execution_arn = start_execution()
    if not execution_arn:
        return
    
    # Monitor execution
    monitor_execution(execution_arn)
    
    # Get execution history
    get_execution_history(execution_arn)
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)
    
    print("\n📋 Next steps:")
    print("1. Check AWS Console → Step Functions → Executions")
    print("2. Review CloudWatch Logs for each Lambda function")
    print("3. Verify ServiceNow ticket was updated")
    print("4. Check if notification was sent")
    print("\n")

if __name__ == '__main__':
    main()
