class FTPHandler:
    def __init__(self, host, port=21, username='', password=''):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None

    def connect(self):
        import ftplib
        self.connection = ftplib.FTP()
        self.connection.connect(self.host, self.port)
        self.connection.login(self.username, self.password)

    def upload_file(self, file_path, remote_path):
        with open(file_path, 'rb') as file:
            self.connection.storbinary(f'STOR {remote_path}', file)

    def download_file(self, remote_path, local_path):
        with open(local_path, 'wb') as file:
            self.connection.retrbinary(f'RETR {remote_path}', file.write)

    def close(self):
        if self.connection:
            self.connection.quit()