import dataclasses
import os.path
import sys

import bcrypt
from sqlalchemy.orm import Session

from backend.file_server.src.providers.EncryptionProvider import EncryptionProvider
from globals import parse_pkt, create_pkt_line, ResponseCode
from backend.models import User, Repository


def is_directory_traversal(safe_dir: str, value: str):
    """Check if the user tried a directory traversal"""
    return os.path.commonprefix((os.path.realpath(value), safe_dir)) != safe_dir


@dataclasses.dataclass
class AuthenticatedUser:
    id: str
    is_owner: bool
    branch: str


class AuthenticationProvider:
    def __init__(self, conn, db_session: Session, enc: EncryptionProvider, repos_location: str):
        self.conn = conn
        self.db_session = db_session
        self.enc = enc
        self.repos_abs_path = repos_location

    def authenticate_user(self):
        """Authenticate user, uses recv"""
        login_command, data = parse_pkt(self.enc.decrypt_incoming_packet())
        if login_command != "stash-login":
            self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.ERROR, "stash: Unauthenticated")))
            self.conn.close()
            sys.exit(1)
        d = data.decode().split("@")

        if len(d) != 4:
            self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.ERROR, "stash: Invalid Login "
                                                                                       "credentials")))
            self.conn.close()
            sys.exit(1)

        username, repo_name, branch, password = d

        db_user = self.db_session.query(User).where(User.username == username).one_or_none()

        if db_user is None:
            self.conn.send(self.enc.encrypt_packet(
                create_pkt_line(ResponseCode.ERROR, "stash: Login credentials are invalid")))
            self.conn.close()
            sys.exit(1)

        if not bcrypt.checkpw(password.encode(), db_user.password):
            self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.ERROR, "stash: Login "
                                                                                       "credentials are "
                                                                                       "invalid")))
            self.conn.close()
            sys.exit(1)

        repo = self.db_session.query(Repository).where(
            Repository.name == repo_name.removesuffix(".stash"), Repository.user_id == db_user.id).one_or_none()

        if repo is None:
            self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.ERROR, "stash: No related repository "
                                                                                       "was found")))
            self.conn.close()
            sys.exit(1)

        if is_directory_traversal(os.path.join(self.repos_abs_path, repo.id), os.path.join(self.repos_abs_path, repo.id, "refs", "head", branch)):
            self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.ERROR, "stash: Invalid branch.")))
            self.conn.close()
            sys.exit(1)

        if not os.path.exists(os.path.join(self.repos_abs_path, repo.id, "refs", "head", branch)):
            with open(os.path.join(self.repos_abs_path, repo.id, "refs", "head", branch), "w") as f:
                f.write("")

        self.conn.send(self.enc.encrypt_packet(create_pkt_line(ResponseCode.AUTHORIZED, "stash: login successful")))

        own_this_repo = repo.user.id == db_user.id

        return repo.id, AuthenticatedUser(is_owner=own_this_repo, id=db_user.id, branch=branch)
