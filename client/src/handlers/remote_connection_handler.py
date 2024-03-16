
import socket

from handlers.encryption_handler import EncryptionHandler
from models.commit import Commit


def create_pkt_line(command_name: str, data: str):
    """Encodes the data to pkt line format"""
    d = f"{str(len(command_name)).zfill(4)}{command_name}\n{str(len(data)).zfill(4)}{data}\n0000"
    return d.encode()


class RemoteConnectionHandler:
    """Handles remote repository connections, and provides useful functions."""

    def __init__(self, url: str):
        self.repo_url = url.rstrip("/")
        self.socket = socket.socket()
        self.handler = EncryptionHandler(self.socket)

    def connect(self):
        """Connect to remote server"""
        self.socket.connect(('127.0.0.1', 8838))
        self.handler.exchange_keys()
        self.socket.send(self.handler.encrypt_packet(create_pkt_line("stash-receive-pack", "abcdefgh")))

    def close(self):
        """Closes the connection to the server"""
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
