from pyDH import pyDH

from backend.file_server.src.providers.AuthenticationProvider import AuthenticationProvider
from backend.file_server.src.providers.EncryptionProvider import EncryptionProvider


###
# Packet line format

# command_name\n
# data\n
# 0000

###

def parse_pkt(data: str) -> (str, str):
    """Parses the pkt line format to command name, data"""
    d = data.split("\n")
    return d[0], d[1]


def create_pkt_line(command_name: str, data: str):
    """Encodes the data to pkt line format"""
    d = f"{command_name}\n{data}\n0000"
    return d.encode()


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
        self.auth.authenticate_user()
