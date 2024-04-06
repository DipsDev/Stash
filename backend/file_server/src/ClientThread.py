import hashlib
import zlib

from pyDH import pyDH

from backend.models import PullRequest
from providers import AuthenticationProvider, EncryptionProvider, FileSystemProvider
from globals import parse_pkt, create_pkt_line, ResponseCode


###
# Packet line format

# command_name\n
# data

###


class ClientThread:
    def __init__(self, conn, db_session):
        self.user = None
        self.file_system = None

        self.conn = conn
        self.db_session = db_session
        self.df = pyDH.DiffieHellman()
        self.enc = EncryptionProvider(self.conn)
        self.auth = AuthenticationProvider(self.conn, self.db_session, self.enc)
        self.repo_id = None
        self.file_system: FileSystemProvider
        self.buffer = []

    def __handle_client(self):
        """Handle client command communications"""
        command_name, data = parse_pkt(self.enc.decrypt_incoming_packet())

        if command_name == ResponseCode.RECEIVE_OBJECT.value:
            data = data.decode()
            data = self.file_system.get_server_object(data[:2], data[2:])
            self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.SEND_OBJECT, data)))
            return

        if command_name == ResponseCode.RECEIVE_HEAD_COMMIT.value:
            data = data.decode()
            data = self.file_system.get_head_commit(data)
            self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.SEND_OBJECT, data)))
            return

        if command_name == ResponseCode.UPDATE_HEAD.value:
            head_cmt = data.decode()
            if not self.user.is_owner:
                # Create a pull request here
                pr_id = hashlib.md5(f"{self.repo_id[:10]}{head_cmt[:65]}")
                created_pull_request = PullRequest(id=pr_id,
                                                   repo_id=self.repo_id,
                                                   head_hash=head_cmt,
                                                   user_id=self.user.id)
                self.conn.send(self.enc.encrypt_packet(
                    create_pkt_line(ResponseCode.OK, "stash: Pull request created.")))
                return

            self.file_system.update_head_commit("main", head_cmt)
            self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.OK,
                                                                   f"stash: Remote branch updated."
                                                                   f" '{'main'}' is up to date")))
            return

        if command_name == ResponseCode.SEND_STREAM.value:
            # Add to the buffer
            self.buffer.append(data)
            return

        if command_name == ResponseCode.SEND_PACKFILE.value:
            if len(self.buffer) > 0:
                data = zlib.decompress(b"".join(self.buffer))
                self.buffer.clear()
            try:
                self.file_system.execute_packfile(data)
            except Exception as e:
                print(e)
                self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.ERROR, "stash: Uploading failed")))
            finally:
                self.conn.send(
                    self.enc.encrypt_packet(create_pkt_line(ResponseCode.OK, "stash: Uploading was successful")))
            return

        self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.ERROR, "stash: Unknown command")))

    def run(self):
        """Client thread main loop"""
        # Exchange cryptography keys, and establish a secured session
        self.enc.exchange_keys()

        # Authenticate user
        self.repo_id, self.user = self.auth.authenticate_user()
        self.file_system = FileSystemProvider(r"D:\code\stash\backend\__temp__", self.repo_id)

        while True:
            self.__handle_client()
