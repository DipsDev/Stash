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
    def __init__(self, conn, db_session, repos_loc: str):
        self.user = None
        self.file_system = None
        self.repos_abs_path = repos_loc

        self.conn = conn
        self.db_session = db_session
        self.df = pyDH.DiffieHellman()
        self.enc = EncryptionProvider(self.conn)
        self.auth = AuthenticationProvider(self.conn, self.db_session, self.enc, repos_loc)
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

            self.file_system.update_head_commit(self.user.branch, head_cmt)
            self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.OK,
                                                                   f"stash: Remote branch updated."
                                                                   f" '{self.user.branch}' is up to date")))
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

        self.file_system = FileSystemProvider(self.repos_abs_path, self.repo_id)

        while True:
            self.__handle_client()
