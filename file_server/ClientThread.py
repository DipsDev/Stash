from pyDH import pyDH

from file_server.providers.EncryptionProvider import EncryptionProvider


###
# Packet line format
# (length [4 bytes])command_name\n
# (length [4 bytes])data\n
# 0000
###

class ClientThread:
    def __init__(self, conn):
        self.conn = conn
        self.df = pyDH.DiffieHellman()
        self.enc = EncryptionProvider(self.conn)

    def run(self):
        self.enc.exchange_keys()
        print(self.enc.decrypt_incoming_packet())
