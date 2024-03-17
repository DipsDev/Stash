import socket
import sys

from handlers.encryption_handler import EncryptionHandler
from models.commit import Commit


def create_pkt_line(command_name: str, data: str):
    """Encodes the data to pkt line format"""
    d = f"{command_name}\n{data}\n0000"
    return d.encode()


def parse_pkt(data: str) -> (str, str):
    """Parses the pkt line format to command name, data"""
    d = data.split("\n")
    return d[0], d[1]


class RemoteConnectionHandler:
    """Handles remote repository connections, and provides useful functions."""

    def __init__(self, url: str):
        self.repo_url = url.rstrip("/")
        self.socket = socket.socket()
        self.handler = EncryptionHandler(self.socket)

    def connect(self):
        """Connect to remote web_server"""
        self.socket.connect(('127.0.0.1', 8838))
        self.handler.exchange_keys()
        login_info = input("stash: Provide your login details, separated by a @: ")
        self.socket.send(self.handler.encrypt_packet(create_pkt_line("stash-login", login_info)))

        pkt_command, pkt_data = parse_pkt(self.handler.decrypt_incoming_packet())
        if pkt_command == "stash-error":
            print(pkt_data)
            sys.exit(1)

    def close(self):
        """Closes the connection to the web_server"""
        self.socket.close()

    def get_remote_head_commit(self, branch: str):
        """Get remote head commit"""
        raise NotImplementedError()

    def resolve_remote_object(self, sha1: str):
        """Resolve a remote object"""
        raise NotImplementedError()

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
