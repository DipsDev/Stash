from pyDH import pyDH
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class EncryptionHandler:
    def __init__(self, socket):
        self.socket = socket
        self.df = None
        self.aes = None

    def exchange_keys(self):
        """Exchange keys between parties, and create a shared key"""
        self.df = pyDH.DiffieHellman()
        self.socket.send(str(self.df.gen_public_key()).encode())
        server_pub = int(self.socket.recv(1024).decode())
        shared = self.df.gen_shared_key(server_pub)
        self.generate_aes(shared)

    def generate_aes(self, shared: str):
        """Creates aes symmetric key"""
        self.aes = AES.new(bytes.fromhex(shared), AES.MODE_ECB)

    def decrypt_incoming_packet(self) -> str:
        """Decrypts incoming packets, uses recv"""
        encrypted_data_length = self.socket.recv(4)
        encrypted_data = self.socket.recv(int(encrypted_data_length))
        return unpad(self.aes.decrypt(encrypted_data), 32).decode()

    def encrypt_packet(self, data: bytes) -> bytes:
        """Encrypts the packet, and prefixes with the length"""
        encrypted_data = self.aes.encrypt(pad(data, 32))
        return f"{str(len(encrypted_data)).zfill(4)}".encode() + encrypted_data
