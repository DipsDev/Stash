import socket
import threading


from file_server.ClientThread import ClientThread

# Packet line
# Hexadecimal length is added before sending

PORT = 8838


class Server:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('127.0.0.1', PORT))

    def listen(self):
        self.s.listen()
        while 1:
            conn, addr = self.s.accept()
            thrd = ClientThread(conn)
            threading.Thread(daemon=False, target=thrd.run).start()


Server().listen()
