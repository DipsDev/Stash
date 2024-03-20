import socket
import sys
import zlib
import getpass

from handlers.encryption_handler import EncryptionHandler
from models.commit import Commit


def create_pkt_line(command_name: str, data: str | bytes):
    """Encodes the data to pkt line format"""
    command_name_length = str(len(command_name)).zfill(4)
    if type(data) == str:
        d = f"{command_name_length}{command_name}\n{data}"
        return d.encode()

    d = f"{command_name_length}{command_name}\n".encode() + data
    return d


def parse_pkt(data: bytes, binary_data=False) -> (str, str):
    """Parses the pkt line format to command name, data"""
    if not binary_data:
        data = data.decode()
        header_length = int(data[:4])
        header = data[4:4 + header_length]
        return header, data[5 + header_length::]

    header_length = int(data[:4].decode())
    header = data[4:4 + header_length].decode()
    return header, zlib.decompress(data[5 + header_length::]).decode()


class RemoteConnectionHandler:
    """Handles remote repository connections, and provides useful functions."""

    def __init__(self, url: str):
        self.repo_url = url.rstrip("/")
        self.socket = socket.socket()
        self.handler = EncryptionHandler(self.socket)

    def generate_pack_file(self, prep_file: str):
        """Generates a packfile from a prep file
        prep files usually look like:

        sha1 type
        """
        pack_file = ""
        prep_file = prep_file.split("\n")

    def connect(self):
        """Connect to remote web_server"""
        self.socket.connect(('127.0.0.1', 8838))

        self.handler.exchange_keys()

        username = input("stash: Please provide your username: ")
        password = getpass.getpass(f"{username}@stash's password: ")

        self.socket.send(self.handler.encrypt_packet(create_pkt_line("stash-login", f"{username}@{password}")))

        pkt_command, pkt_data = parse_pkt(self.handler.decrypt_incoming_packet())
        if pkt_command == "stash-error":
            print(pkt_data)
            self.close()

    def close(self):
        """Closes the connection to the web_server"""
        self.socket.close()
        sys.exit(1)

    def get_remote_head_commit(self, branch: str):
        """Get remote head commit"""

        self.socket.send(self.handler.encrypt_packet(create_pkt_line("stash-receive-head-commit", branch)))

        command_name, data = parse_pkt(self.handler.decrypt_incoming_packet())
        if command_name != "stash-send-object":
            print(data)
            self.close()
        return data

    def resolve_remote_object(self, sha1: str):
        """Resolve a remote object"""
        self.socket.send(self.handler.encrypt_packet(create_pkt_line("stash-receive-object", sha1)))

        temp = self.handler.decrypt_incoming_packet()
        command_name, data = parse_pkt(temp, binary_data=True)
        if command_name != "stash-send-object":
            print("stash: Unexpected error")
            self.close()
        return data

    def resolve_remote_commit_data(self, sha1):
        cmt = self.resolve_remote_object(sha1)
        lines = cmt.split("\n")
        del lines[2]

        assert lines[0][0:6] == "parent"
        parent_hash = lines[0][7::]

        assert lines[1][0:4] == "tree"
        tree_hash = lines[1][5::]

        message = lines[2]

        return Commit(message, tree_hash=tree_hash, parent=parent_hash)
