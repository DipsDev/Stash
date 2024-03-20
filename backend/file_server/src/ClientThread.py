from pyDH import pyDH

from backend.file_server.src.providers.AuthenticationProvider import AuthenticationProvider
from backend.file_server.src.providers.EncryptionProvider import EncryptionProvider
from globals import parse_pkt, create_pkt_line, ResponseCode
from providers.FileSystemProvider import FileSystemProvider


###
# Packet line format

# command_name\n
# data

###


class ClientThread:
    def __init__(self, conn, db_session):
        self.conn = conn
        self.db_session = db_session
        self.df = pyDH.DiffieHellman()
        self.enc = EncryptionProvider(self.conn)
        self.auth = AuthenticationProvider(self.conn, self.db_session, self.enc)
        self.file_system = FileSystemProvider(r"D:\code\stash\backend\__temp__")

    def __handle_client(self):
        """Handle client command communications"""
        command_name, data = parse_pkt(self.enc.decrypt_incoming_packet())

        if command_name == ResponseCode.RECEIVE_OBJECT.value:
            data = data.decode()
            data = self.file_system.get_server_object("1ab7698a1f0ff0ce9796c8ed2fe10c55f0ede06d", data[:2], data[2:])
            self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.SEND_OBJECT, data)))
            return

        if command_name == ResponseCode.RECEIVE_HEAD_COMMIT.value:
            data = data.decode()
            data = self.file_system.get_head_commit("1ab7698a1f0ff0ce9796c8ed2fe10c55f0ede06d", data)
            self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.SEND_OBJECT, data)))
            return

        if command_name == ResponseCode.UPDATE_HEAD.value:
            self.file_system.update_head_commit("1ab7698a1f0ff0ce9796c8ed2fe10c55f0ede06d", "main", data.decode())
            self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.OK,
                                                                   f"stash: Remote branch updated."
                                                                   f" '{'main'}' is up to date")))
            return

        if command_name == ResponseCode.SEND_PACKFILE.value:
            try:
                self.file_system.execute_packfile("1ab7698a1f0ff0ce9796c8ed2fe10c55f0ede06d", data)
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
        self.auth.authenticate_user()

        while True:
            self.__handle_client()
