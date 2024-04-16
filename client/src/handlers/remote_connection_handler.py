import os
import socket
import zlib
import getpass
import configparser

import objects
from handlers.encryption_handler import EncryptionHandler
from handlers.logger_handler import Logger
from models.commit import Commit


def parse_pkt(data: bytes, bypass_decompress=False) -> (str, str):
    """Parses the pkt line format to command name, data"""
    is_compressed = bool(int(data[:1].decode()))
    header_length = int(data[1:5].decode())
    header = data[5:5 + header_length].decode()

    if bypass_decompress:
        return header, data[6 + header_length::]

    if not is_compressed:
        return header, data[6 + header_length::].decode()

    return header, zlib.decompress(data[6 + header_length::]).decode()


def create_pkt_line(command_name: str, data: str | bytes):
    """Encodes the data to pkt line format"""
    command_name_length = str(len(command_name)).zfill(4)
    if type(data) == str:
        d = f"{0}{command_name_length}{command_name}\n{data}"
        return d.encode()

    d = f"{1}{command_name_length}{command_name}\n".encode() + data
    return d


class RemoteConnectionHandler:
    """Handles remote repository connections, and provides useful functions."""

    def __init__(self, full_repo: str):
        self.full_repo = full_repo
        self.socket = socket.socket()
        self.handler = EncryptionHandler(self.socket)
        self.config = configparser.ConfigParser()
        self.config_created = False

    def reload_local_remotes(self, path: str = None):
        """Reads the config file again, and reloads the content to the memory."""
        self.config.read(os.path.join(path, "config") if path is not None else os.path.join(self.full_repo, "config"))
        self.config_created = True

    def commit_config_changes(self, path: str = None):
        """Applies the changes to the config"""
        if not self.config_created:
            self.reload_local_remotes()
        with open(os.path.join(path if path is not None else self.full_repo, "config"), "w") as f:
            self.config.write(f)

    def get_available_remotes(self) -> list[str]:
        """Returns a list of the available remotes"""
        if not self.config_created:
            self.reload_local_remotes()
        remotes = []
        for key in self.config.sections():
            remotes.append(key[8:len(key) - 1])
        return remotes

    def add_remote(self, remote_name: str, url: str, path: str = None):
        """Adds a remote to the config"""
        if not self.config_created:
            self.reload_local_remotes()
        try:
            self.config.add_section(f'remote "{remote_name}"')
        except configparser.DuplicateSectionError:
            Logger.error(f"stash: Remote '{remote_name}' is already exists.")
            quit(1)
        self.config[f"remote \"{remote_name}\""]["url"] = url
        self.commit_config_changes(path)

    def is_remote_exists(self, remote_name: str) -> bool:
        """Returns True or False whether the given remote_name exists"""
        if not self.config_created:
            self.reload_local_remotes()
        return self.config.has_section(f'remote "{remote_name}"')

    def get_option(self, remote_name: str, option: str):
        """Returns the option of a section"""
        if not self.config_created:
            self.reload_local_remotes()

        if not self.is_remote_exists(remote_name):
            Logger.error("stash: Remote does not exists. see 'stash help remote' for help.")
            quit(1)
        return self.config[f'remote "{remote_name}"'][option]

    def get_remote(self, remote_name: str):
        if not self.config_created:
            self.reload_local_remotes()

        if not self.is_remote_exists(remote_name):
            Logger.error("stash: Remote does not exists. see 'stash help remote' for help.")
            quit(1)
        return self.config[f'remote "{remote_name}"']

    def generate_pack_file(self, prep_file: str):
        """Generates a packfile from a prep file
        prep files usually look like:

        sha1 type
        """
        pack_file = b""
        prep_file = prep_file.split("\n")
        del prep_file[-1]

        MAX_DIGIT_SIZE = 8  # 12mb
        for row in prep_file:
            sha, obj_type = row.split(" ")
            loc = objects.resolve_object_location(self.full_repo, sha)
            data = objects.read_file(loc, binary_=True)
            pack_file += f"{sha} {str(len(data)).zfill(MAX_DIGIT_SIZE)}".encode() + data + "\n".encode()

        return zlib.compress(pack_file)

    def push_pkt(self, code: str, obj: bytes | str):
        """Sends a pkt file to the server"""
        if len(obj) > 8000:  # Check if data is bigger than max buffer size
            index = 0
            while index < len(obj):
                self.socket.send(
                    self.handler.encrypt_packet(create_pkt_line("stash-send-stream", obj[index:index + 1010])))
                index += 1010
            self.socket.send(self.handler.encrypt_packet(create_pkt_line(code, "end")))
            return

        else:
            pkt = create_pkt_line(code, obj)
            self.socket.send(self.handler.encrypt_packet(pkt))

        response_code, data = parse_pkt(self.handler.decrypt_incoming_packet())
        if response_code != "stash-ok":
            print(data)
            exit(1)
        return data

    def download_remote_object(self, sha: str):
        """Download remote data"""
        data = self.resolve_remote_object(sha, bypass_decompress=True)
        fd_path = os.path.join(self.full_repo, "objects", sha[:2])
        if not os.path.exists(fd_path):
            os.mkdir(fd_path)

        objects.write_file(os.path.join(fd_path, sha[2:]), data, binary_=True)

    def connect(self, repo_fingerprint: str | None, branch: str = None):
        """Connect to remote web_server"""
        self.socket.connect(('127.0.0.1', 8838))

        self.handler.exchange_keys()

        username = repo_fingerprint if repo_fingerprint else input("stash: Please provide your stash fingerprint (ex: "
                                                                   "username@repository.stash): ")
        remote_branch = branch if branch else input("stash: Input your remote branch name (ex 'main'): ")

        password = getpass.getpass(f"{username}'s password: ")

        self.socket.send(
            self.handler.encrypt_packet(create_pkt_line("stash-login", f"{username}@{remote_branch}@{password}")))

        pkt_command, pkt_data = parse_pkt(self.handler.decrypt_incoming_packet())
        if pkt_command == "stash-error":
            print(pkt_data)
            self.close()

    def close(self):
        """Closes the connection to the web_server"""
        self.socket.close()
        exit(0)

    def get_remote_head_commit(self, branch: str):
        """Get remote head commit"""

        self.socket.send(self.handler.encrypt_packet(create_pkt_line("stash-receive-head-commit", branch)))

        command_name, data = parse_pkt(self.handler.decrypt_incoming_packet())
        if command_name != "stash-send-object":
            print(data)
            self.close()
        return data

    def resolve_remote_object(self, sha1: str, bypass_decompress=False):
        """Resolve a remote object"""
        self.socket.send(self.handler.encrypt_packet(create_pkt_line("stash-receive-object", sha1)))

        temp = self.handler.decrypt_incoming_packet()
        command_name, data = parse_pkt(temp, bypass_decompress=bypass_decompress)
        if command_name != "stash-send-object":
            Logger.println("stash: Unexpected error")
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
