class SFTPHandler:
    def __init__(self, host, port=22, username=None, password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None

    def connect(self):
        import paramiko
        try:
            self.connection = paramiko.SFTPClient.from_transport(paramiko.Transport((self.host, self.port)))
            self.connection.connect(username=self.username, password=self.password)
        except Exception as e:
            print(f"Failed to connect to SFTP server: {e}")

    def upload_file(self, local_file_path, remote_file_path):
        if self.connection:
            try:
                self.connection.put(local_file_path, remote_file_path)
                print(f"Uploaded {local_file_path} to {remote_file_path}")
            except Exception as e:
                print(f"Failed to upload file: {e}")

    def download_file(self, remote_file_path, local_file_path):
        if self.connection:
            try:
                self.connection.get(remote_file_path, local_file_path)
                print(f"Downloaded {remote_file_path} to {local_file_path}")
            except Exception as e:
                print(f"Failed to download file: {e}")

    def close(self):
        if self.connection:
            self.connection.close()
            print("Connection closed")