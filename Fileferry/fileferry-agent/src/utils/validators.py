def validate_file_path(file_path):
    import os
    
    if not os.path.isfile(file_path):
        raise ValueError("File path does not exist or is not a file.")
    return True

def validate_sftp_credentials(credentials):
    required_keys = ['host', 'username', 'password']
    for key in required_keys:
        if key not in credentials:
            raise ValueError(f"Missing required SFTP credential: {key}")
    return True

def validate_aws_credentials(credentials):
    required_keys = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION']
    for key in required_keys:
        if key not in credentials:
            raise ValueError(f"Missing required AWS credential: {key}")
    return True

def validate_transfer_job(transfer_job):
    if not isinstance(transfer_job, dict):
        raise ValueError("Transfer job must be a dictionary.")
    
    required_fields = ['source', 'destination', 'status']
    for field in required_fields:
        if field not in transfer_job:
            raise ValueError(f"Missing required field in transfer job: {field}")
    return True

def validate_notification_channel(channel):
    valid_channels = ['email', 'sms', 'teams']
    if channel not in valid_channels:
        raise ValueError(f"Invalid notification channel: {channel}")
    return True