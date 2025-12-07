"""
Lambda Function: Download from S3
Downloads file from S3 and prepares for transfer
"""

import json
import boto3
import hashlib
from typing import Dict, Any


s3_client = boto3.client('s3')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Download file metadata and prepare for transfer
    
    Event structure:
    {
        "transfer_plan": {
            "source_bucket": "my-bucket",
            "source_key": "file.txt"
        }
    }
    """
    
    try:
        transfer_plan = event['transfer_plan']
        bucket = transfer_plan['source_bucket']
        key = transfer_plan['source_key']
        
        print(f"📥 Preparing S3 download: s3://{bucket}/{key}")
        
        # Get object metadata
        metadata = s3_client.head_object(Bucket=bucket, Key=key)
        
        file_size = metadata['ContentLength']
        etag = metadata['ETag'].strip('"')
        last_modified = metadata['LastModified'].isoformat()
        
        # Calculate MD5 for small files
        md5_checksum = None
        if file_size < 100 * 1024 * 1024:  # 100MB
            print("🔢 Calculating MD5 checksum...")
            s3_object = s3_client.get_object(Bucket=bucket, Key=key)
            md5_hash = hashlib.md5()
            
            for chunk in iter(lambda: s3_object['Body'].read(8192), b''):
                md5_hash.update(chunk)
            
            md5_checksum = md5_hash.hexdigest()
            print(f"✅ MD5: {md5_checksum}")
        
        # Determine transfer strategy
        if file_size < 100 * 1024 * 1024:  # 100MB
            transfer_strategy = 'direct'
        elif file_size < 1024 * 1024 * 1024:  # 1GB
            transfer_strategy = 'chunked'
        else:
            transfer_strategy = 'parallel_chunked'
        
        print(f"✅ Download prepared: {file_size} bytes, strategy: {transfer_strategy}")
        
        return {
            'status': 'ready',
            'file_metadata': {
                'bucket': bucket,
                'key': key,
                'size': file_size,
                'etag': etag,
                'md5_checksum': md5_checksum,
                'last_modified': last_modified
            },
            'transfer_strategy': transfer_strategy
        }
        
    except Exception as e:
        print(f"❌ Download preparation error: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }
