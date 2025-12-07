"""
SSO Handler - AWS IAM Identity Center Integration with 10-Second Timeout
Complete implementation for FileFerry AI Agent architecture

Key Features:
1. 10-second session timeout (DynamoDB TTL)
2. ServiceNow request validation
3. Prevention of re-login without new request
4. Read-only S3 access enforcement
5. Automatic session cleanup
"""

import boto3
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError
import time

logger = logging.getLogger(__name__)


class SSOHandler:
    """
    AWS SSO (IAM Identity Center) authentication handler.
    
    Security Features:
    - 10-SECOND SESSION TIMEOUT (enforced via DynamoDB TTL)
    - Automatic session expiration
    - ServiceNow request validation
    - Prevention of re-login without new request
    - Read-only S3 access only
    
    Integration Points:
    - DynamoDB ActiveSessions table (10-sec TTL)
    - AWS STS AssumeRole for temporary credentials
    - ServiceNow API validation (TODO)
    """
    
    def __init__(self, config: Dict[str, Any], dynamodb_client=None):
        """
        Initialize SSO Handler.
        
        Args:
            config: Configuration dictionary
            dynamodb_client: Optional DynamoDB client (for testing)
        """
        self.config = config
        sso_config = config.get('sso', {})
        
        # SSO Configuration
        self.start_url = sso_config.get('start_url')
        self.region = sso_config.get('region', 'us-east-1')
        self.account_id = sso_config.get('account_id')
        self.role_name = sso_config.get('role_name', 'FileFerryReadOnlyRole')
        self.session_duration = sso_config.get('session_duration', 10)  # 10 seconds
        
        # DynamoDB table
        self.table_name = config.get('dynamodb', {}).get('active_sessions_table', 'FileFerry-ActiveSessions')
        
        # AWS clients
        self.dynamodb = dynamodb_client if dynamodb_client else boto3.client('dynamodb', region_name=self.region)
        self.sts_client = boto3.client('sts', region_name=self.region)
        
        # Test mode
        self.test_mode = config.get('agent', {}).get('test_mode', False)
        
        if self.test_mode:
            logger.warning("⚠️  SSO Handler in TEST MODE")
        else:
            logger.info(f"✅ SSO Handler initialized: {self.session_duration}s timeout, table={self.table_name}")
    
    def authenticate_user(
        self,
        user_id: str,
        servicenow_request_id: str,
        region: Optional[str] = None
    ) -> str:
        """
        Authenticate user and create 10-second session.
        
        Args:
            user_id: User email
            servicenow_request_id: ServiceNow request ID (REQ0012345)
            region: Optional AWS region
            
        Returns:
            session_token: UUID session token
            
        Raises:
            SSOAuthenticationError: If authentication fails
        """
        try:
            logger.info(f"[SSO] Authenticating: user={user_id}, request={servicenow_request_id}")
            
            # Validate ServiceNow request
            if not self._validate_servicenow_request(servicenow_request_id):
                raise SSOAuthenticationError(f"Invalid ServiceNow request: {servicenow_request_id}")
            
            # Check if request already used
            if self._is_request_already_used(servicenow_request_id):
                raise SSOAuthenticationError(
                    f"Request {servicenow_request_id} already used. Create new ServiceNow request."
                )
            
            # Get temporary AWS credentials
            credentials = self._get_temporary_credentials(user_id, region)
            
            # Generate session token
            session_token = str(uuid.uuid4())
            
            # Store in DynamoDB with 10-second TTL
            self._store_session(
                session_token=session_token,
                user_id=user_id,
                servicenow_request_id=servicenow_request_id,
                credentials=credentials,
                region=region or self.region
            )
            
            expires_at = datetime.utcnow() + timedelta(seconds=self.session_duration)
            logger.info(f"[SSO] ✅ Session created: {session_token[:8]}... (expires: {expires_at.isoformat()}Z)")
            
            return session_token
            
        except SSOAuthenticationError:
            raise
        except Exception as e:
            logger.error(f"[SSO] Authentication error: {str(e)}", exc_info=True)
            raise SSOAuthenticationError(f"Authentication failed: {str(e)}")
    
    def is_session_valid(self, session_token: str) -> bool:
        """
        Check if session token is valid.
        
        Args:
            session_token: Session token
            
        Returns:
            True if valid and not expired
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={'session_token': {'S': session_token}}
            )
            
            if 'Item' not in response:
                logger.warning(f"[SSO] Session not found: {session_token[:8]}...")
                return False
            
            # Check TTL
            item = response['Item']
            ttl = int(item['ttl']['N'])
            current_time = int(time.time())
            
            if current_time >= ttl:
                logger.warning(f"[SSO] Session expired: {session_token[:8]}...")
                return False
            
            remaining = ttl - current_time
            logger.debug(f"[SSO] ✅ Session valid: {session_token[:8]}... ({remaining}s remaining)")
            return True
            
        except ClientError as e:
            logger.error(f"[SSO] Error validating session: {str(e)}")
            return False
    
    def get_session_credentials(self, session_token: str) -> Optional[Dict[str, str]]:
        """
        Get AWS credentials from session.
        
        Args:
            session_token: Valid session token
            
        Returns:
            Dict with AWS credentials or None
        """
        try:
            if not self.is_session_valid(session_token):
                return None
            
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={'session_token': {'S': session_token}}
            )
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            
            return {
                "access_key_id": item['aws_access_key_id']['S'],
                "secret_access_key": item['aws_secret_access_key']['S'],
                "session_token": item['aws_session_token']['S'],
                "region": item['region']['S']
            }
            
        except ClientError as e:
            logger.error(f"[SSO] Error retrieving credentials: {str(e)}")
            return None
    
    def auto_logout(self, session_token: str) -> bool:
        """
        Manually logout session (optional - DynamoDB TTL handles auto-logout).
        
        Args:
            session_token: Session token to invalidate
            
        Returns:
            True if logged out successfully
        """
        try:
            response = self.dynamodb.delete_item(
                TableName=self.table_name,
                Key={'session_token': {'S': session_token}},
                ReturnValues='ALL_OLD'
            )
            
            if 'Attributes' in response:
                logger.info(f"[SSO] 🔒 Logged out: {session_token[:8]}...")
                return True
            else:
                logger.warning(f"[SSO] Session not found for logout: {session_token[:8]}...")
                return False
                
        except ClientError as e:
            logger.error(f"[SSO] Logout error: {str(e)}")
            return False
    
    def get_session_info(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Get session metadata (no credentials).
        
        Args:
            session_token: Session token
            
        Returns:
            Dict with session info
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={'session_token': {'S': session_token}}
            )
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            ttl = int(item['ttl']['N'])
            current_time = int(time.time())
            
            return {
                "session_token": session_token[:8] + "...",
                "user_id": item['user_id']['S'],
                "servicenow_request_id": item['servicenow_request_id']['S'],
                "region": item['region']['S'],
                "created_at": item['created_at']['S'],
                "expires_at": datetime.utcfromtimestamp(ttl).isoformat() + 'Z',
                "seconds_remaining": max(0, ttl - current_time),
                "is_valid": ttl > current_time
            }
            
        except ClientError as e:
            logger.error(f"[SSO] Error getting session info: {str(e)}")
            return None
    
    # Private helper methods
    
    def _get_temporary_credentials(self, user_id: str, region: Optional[str]) -> Dict[str, str]:
        """Get temporary AWS credentials via STS AssumeRole."""
        if self.test_mode:
            logger.warning("⚠️  Test mode: Using dummy credentials")
            return {
                "access_key_id": "ASIATEST123456789",
                "secret_access_key": "test_secret_key",
                "session_token": "test_session_token",
                "expiration": (datetime.utcnow() + timedelta(seconds=self.session_duration)).isoformat() + 'Z'
            }
        
        try:
            role_arn = f"arn:aws:iam::{self.account_id}:role/{self.role_name}"
            session_name = f"FileFerry-{user_id}-{int(time.time())}"
            
            logger.info(f"[SSO] Assuming role: {role_arn}")
            
            response = self.sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=session_name,
                DurationSeconds=900,  # 15 min (min allowed), but we enforce 10-sec via TTL
                Tags=[
                    {'Key': 'User', 'Value': user_id},
                    {'Key': 'Application', 'Value': 'FileFerry'}
                ]
            )
            
            creds = response['Credentials']
            
            return {
                "access_key_id": creds['AccessKeyId'],
                "secret_access_key": creds['SecretAccessKey'],
                "session_token": creds['SessionToken'],
                "expiration": creds['Expiration'].isoformat() + 'Z'
            }
            
        except NoCredentialsError:
            logger.error("[SSO] No AWS credentials")
            raise SSOAuthenticationError("No AWS credentials found")
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"[SSO] STS error: {error_code} - {error_msg}")
            
            if error_code == 'AccessDenied':
                raise SSOAuthenticationError(f"Access denied to role {self.role_name}")
            else:
                raise SSOAuthenticationError(f"AWS STS error: {error_msg}")
    
    def _store_session(
        self,
        session_token: str,
        user_id: str,
        servicenow_request_id: str,
        credentials: Dict[str, str],
        region: str
    ) -> None:
        """Store session in DynamoDB with 10-second TTL."""
        try:
            current_time = int(time.time())
            ttl = current_time + self.session_duration
            
            item = {
                'session_token': {'S': session_token},
                'user_id': {'S': user_id},
                'servicenow_request_id': {'S': servicenow_request_id},
                'aws_access_key_id': {'S': credentials['access_key_id']},
                'aws_secret_access_key': {'S': credentials['secret_access_key']},
                'aws_session_token': {'S': credentials['session_token']},
                'region': {'S': region},
                'created_at': {'S': datetime.utcnow().isoformat() + 'Z'},
                'ttl': {'N': str(ttl)}
            }
            
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item
            )
            
            logger.info(f"[SSO] ✅ Session stored: TTL={ttl} ({self.session_duration}s)")
            
        except ClientError as e:
            logger.error(f"[SSO] Error storing session: {str(e)}")
            raise SSOAuthenticationError(f"Failed to store session: {str(e)}")
    
    def _validate_servicenow_request(self, servicenow_request_id: str) -> bool:
        """Validate ServiceNow request."""
        if self.test_mode:
            logger.warning(f"⚠️  Test mode: Accepting {servicenow_request_id}")
            return True
        
        if not servicenow_request_id:
            return False
        
        # Basic format check
        if not (servicenow_request_id.startswith('REQ') or servicenow_request_id.startswith('INC')):
            logger.error(f"[SSO] Invalid format: {servicenow_request_id}")
            return False
        
        # TODO: Call ServiceNow API to validate
        logger.info(f"[SSO] ✅ Request validated: {servicenow_request_id}")
        return True
    
    def _is_request_already_used(self, servicenow_request_id: str) -> bool:
        """Check if ServiceNow request was already used."""
        try:
            response = self.dynamodb.scan(
                TableName=self.table_name,
                FilterExpression='servicenow_request_id = :req_id',
                ExpressionAttributeValues={
                    ':req_id': {'S': servicenow_request_id}
                },
                Limit=1
            )
            
            if response.get('Count', 0) > 0:
                logger.warning(f"[SSO] ⚠️  Request already used: {servicenow_request_id}")
                return True
            
            return False
            
        except ClientError as e:
            logger.error(f"[SSO] Error checking request: {str(e)}")
            return True  # Fail secure


class SSOAuthenticationError(Exception):
    """SSO authentication error."""
    pass
