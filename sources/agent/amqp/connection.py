from amqp import Connection
import certifi

__all__ = ['ConnectionFabric']


class ConnectionFabric:
    
    def __init__(self, host: str, 
                 login: str, password: str,
                 virtual_host: str, ssl: bool):
        self.host = host
        self.login = login
        self.password = password
        self.virtual_host = virtual_host
        self.ssl = {'ca_certs': certifi.where()} if ssl else False

    
    def create_connection(self):
        return Connection(
            host=self.host,
            userid=self.login,
            password=self.password,
            virtual_host=self.virtual_host,
            confirm_publish=True,
            ssl=self.ssl
        )
