from pyDH import pyDH

from file_server.providers.AuthenticationProvider import AuthenticationProvider
from file_server.providers.EncryptionProvider import EncryptionProvider


###
# Packet line format

# command_name\n
# data\n
# 0000

###

class ClientThread:
    def __init__(self, conn):
        self.conn = conn
        self.df = pyDH.DiffieHellman()
        self.enc = EncryptionProvider(self.conn)
        self.auth = AuthenticationProvider(self.conn)

    def run(self):
        # Exchange cryptography keys, and establish a secured session
        self.enc.exchange_keys()

        print(self.enc.decrypt_incoming_packet())
