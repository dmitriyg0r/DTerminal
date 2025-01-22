import paramiko
import logging
import os

class SSHConnection:
    def __init__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connected = False
    
    def connect(self, hostname, username, password=None, key_filename=None):
        try:
            # Настраиваем логирование
            logging.basicConfig(level=logging.INFO)
            paramiko_logger = logging.getLogger("paramiko")
            paramiko_logger.setLevel(logging.INFO)

            connect_kwargs = {
                'hostname': hostname,
                'username': username,
                'timeout': 10
            }

            # Если указан пароль, используем его
            if password:
                connect_kwargs.update({
                    'password': password,
                    'look_for_keys': False,
                    'allow_agent': False
                })
            # Если указан путь к ключу и файл существует, используем его
            elif key_filename and os.path.exists(os.path.expanduser(key_filename)):
                connect_kwargs.update({
                    'key_filename': os.path.expanduser(key_filename),
                    'look_for_keys': True,
                    'allow_agent': True
                })
            # Если нет ни пароля, ни валидного ключа - пробуем использовать стандартные ключи
            else:
                connect_kwargs.update({
                    'look_for_keys': True,
                    'allow_agent': True
                })

            # Пытаемся подключиться
            self.client.connect(**connect_kwargs)
            self.connected = True
            return True
            
        except paramiko.AuthenticationException as e:
            logging.error(f"Ошибка аутентификации: {str(e)}")
            return False
        except paramiko.SSHException as e:
            logging.error(f"SSH ошибка: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Ошибка подключения: {str(e)}")
            return False

    def disconnect(self):
        if self.connected:
            self.client.close()
            self.connected = False 