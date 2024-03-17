from pyDH import pyDH

from backend.file_server.src.providers.AuthenticationProvider import AuthenticationProvider
from backend.file_server.src.providers.EncryptionProvider import EncryptionProvider


###
# Packet line format

# command_name\n
# data\n
# 0000

###


class ClientThread:
    def __init__(self, conn, session):
        self.conn = conn
        self.session = session
        self.df = pyDH.DiffieHellman()
        self.enc = EncryptionProvider(self.conn)
        self.auth = AuthenticationProvider(self.conn, self.session, self.enc)

    def run(self):
        # Exchange cryptography keys, and establish a secured session
        self.enc.exchange_keys()

        # Authenticate user
        self.auth.authenticate_user()
