class S3Handler:
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name):
        import boto3
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )

    def upload_file(self, file_name, bucket_name, object_name=None):
        if object_name is None:
            object_name = file_name
        try:
            response = self.s3_client.upload_file(file_name, bucket_name, object_name)
            return response
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None

    def download_file(self, bucket_name, object_name, file_name):
        try:
            self.s3_client.download_file(bucket_name, object_name, file_name)
        except Exception as e:
            print(f"Error downloading file: {e}")

    def list_files(self, bucket_name):
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name)
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception as e:
            print(f"Error listing files: {e}")
            return []

    def delete_file(self, bucket_name, object_name):
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_name)
        except Exception as e:
            print(f"Error deleting file: {e}")