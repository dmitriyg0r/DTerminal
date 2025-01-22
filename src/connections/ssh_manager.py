import paramiko

class SSHConnection:
    def __init__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    def connect(self, hostname, username, password=None, key_filename=None):
        try:
            self.client.connect(
                hostname=hostname,
                username=username,
                password=password,
                key_filename=key_filename
            )
            return True
        except Exception as e:
            return False 