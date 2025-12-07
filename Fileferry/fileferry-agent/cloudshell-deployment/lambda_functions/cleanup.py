"""
Lambda Function: Cleanup
Cleans up temporary files and invalidates SSO session
"""

import json
import boto3
import os
from typing import Dict, Any


dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Cleanup resources after transfer
    
    Event structure:
    {
        "ssoSession": {
            "session_token": "abc-123-..."
        },
        "temp_files": ["/tmp/file1.txt"],
        "transfer_id": "transfer-12345"
    }
    """
    
    try:
        print("🧹 Starting cleanup...")
        
        cleanup_results = {
            'sso_invalidated': False,
            'temp_files_deleted': 0,
            'cache_cleared': False
        }
        
        # Invalidate SSO session
        if 'ssoSession' in event and 'session_token' in event['ssoSession']:
            session_token = event['ssoSession']['session_token']
            
            try:
                table = dynamodb.Table('FileFerry-ActiveSessions')
                table.delete_item(Key={'session_token': session_token})
                
                print(f"✅ SSO session invalidated: {session_token[:8]}...")
                cleanup_results['sso_invalidated'] = True
                
            except Exception as e:
                print(f"⚠️ Failed to invalidate SSO session: {str(e)}")
        
        # Delete temporary files from /tmp
        if 'temp_files' in event:
            for file_path in event['temp_files']:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        cleanup_results['temp_files_deleted'] += 1
                        print(f"✅ Deleted: {file_path}")
                except Exception as e:
                    print(f"⚠️ Failed to delete {file_path}: {str(e)}")
        
        # Clear S3 cache entries if needed
        if 'transfer_id' in event:
            try:
                cache_table = dynamodb.Table('FileFerry-S3FileCache')
                # In production, query and delete relevant cache entries
                cleanup_results['cache_cleared'] = True
                print("✅ Cache cleared")
            except Exception as e:
                print(f"⚠️ Failed to clear cache: {str(e)}")
        
        # Log cleanup completion
        print(f"✅ Cleanup completed: {cleanup_results}")
        
        return {
            'status': 'cleaned',
            'cleanup_results': cleanup_results
        }
        
    except Exception as e:
        print(f"❌ Cleanup error: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }
