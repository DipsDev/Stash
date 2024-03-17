import socket
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


from backend.file_server.src.ClientThread import ClientThread

# Packet line
# Hexadecimal length is added before sending

PORT = 8838


class Server:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('127.0.0.1', PORT))
        self.engine = create_engine(r"sqlite:///../../db.sqlite")

    def listen(self):
        self.s.listen()
        with Session(self.engine) as session:
            while 1:
                conn, addr = self.s.accept()
                thrd = ClientThread(conn, session)
                threading.Thread(daemon=False, target=thrd.run).start()


Server().listen()
