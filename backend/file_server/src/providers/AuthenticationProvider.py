from sqlalchemy.orm import Session

from backend.file_server.src.ClientThread import parse_pkt, create_pkt_line
from backend.file_server.src.providers.EncryptionProvider import EncryptionProvider
from services.models import User


class AuthenticationProvider:
    def __init__(self, conn, db_session: Session, enc: EncryptionProvider):
        self.conn = conn
        self.db_session = db_session
        self.enc = enc

    def authenticate_user(self):
        """Authenticate user, uses recv"""
        login_command, data = parse_pkt(self.enc.decrypt_incoming_packet())
        if login_command != "stash-login":
            self.conn.send(create_pkt_line("stash-error", "stash: Login credentials are invalid."))
            self.conn.close()
            return
        username, password = data.split("@")
        db_user = self.db_session.query(User.username == username).first()
        print(db_user)
