"""
Lambda Function: Transfer to FTP
Executes S3→FTP transfer with streaming
"""

import json
import boto3
import hashlib
from ftplib import FTP
from typing import Dict, Any


s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Transfer file from S3 to FTP/SFTP
    
    Event structure:
    {
        "transfer_plan": {
            "source_bucket": "my-bucket",
            "source_key": "file.txt",
            "destination_host": "ftp.example.com",
            "destination_port": 21,
            "destination_username": "user",
            "destination_password": "pass",
            "destination_path": "/uploads",
            "transfer_type": "ftp"
        },
        "file_metadata": {
            "size": 1024,
            "md5_checksum": "abc123..."
        }
    }
    """
    
    try:
        transfer_plan = event['transfer_plan']
        file_metadata = event['file_metadata']
        
        bucket = transfer_plan['source_bucket']
        key = transfer_plan['source_key']
        
        print(f"🚀 Starting transfer: s3://{bucket}/{key}")
        
        # Connect to FTP
        ftp = FTP()
        ftp.connect(
            transfer_plan['destination_host'],
            transfer_plan.get('destination_port', 21)
        )
        ftp.login(
            transfer_plan.get('destination_username', 'anonymous'),
            transfer_plan.get('destination_password', '')
        )
        
        # Change to destination directory
        if 'destination_path' in transfer_plan:
            try:
                ftp.cwd(transfer_plan['destination_path'])
            except:
                # Create directory if it doesn't exist
                ftp.mkd(transfer_plan['destination_path'])
                ftp.cwd(transfer_plan['destination_path'])
        
        # Stream from S3 to FTP
        s3_object = s3_client.get_object(Bucket=bucket, Key=key)
        s3_stream = s3_object['Body']
        
        remote_filename = key.split('/')[-1]
        bytes_transferred = 0
        checksum = hashlib.md5()
        
        def read_callback(data):
            nonlocal bytes_transferred
            bytes_transferred += len(data)
            checksum.update(data)
            
            # Log progress every 10MB
            if bytes_transferred % (10 * 1024 * 1024) == 0:
                print(f"📊 Progress: {bytes_transferred / 1024 / 1024:.2f} MB transferred")
        
        # Upload with chunked reading
        ftp.storbinary(
            f'STOR {remote_filename}',
            s3_stream,
            blocksize=8192,
            callback=read_callback
        )
        
        ftp.quit()
        
        print(f"✅ Transfer completed: {bytes_transferred} bytes")
        
        # Verify checksum if available
        checksum_match = None
        if file_metadata.get('md5_checksum'):
            checksum_match = (checksum.hexdigest() == file_metadata['md5_checksum'])
            print(f"🔍 Checksum match: {checksum_match}")
        
        return {
            'status': 'completed',
            'bytes_transferred': bytes_transferred,
            'md5_checksum': checksum.hexdigest(),
            'checksum_match': checksum_match,
            'remote_path': f"{transfer_plan.get('destination_path', '/')}/{remote_filename}"
        }
        
    except Exception as e:
        print(f"❌ Transfer error: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }
