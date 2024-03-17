from typing import List

from flask_login import UserMixin
from sqlalchemy.orm import Relationship, mapped_column, Mapped
from sqlalchemy import ForeignKey
from .database import db


class AuthenticationKey(db.Model):
    """Model that represents a key that can be used for authentication"""

    id: Mapped[str] = mapped_column(db.String(32), primary_key=True)
    value: Mapped[str] = mapped_column(db.String(32), unique=True)
    description: Mapped[str] = mapped_column(db.String(75))
    user_id: Mapped[str] = mapped_column(db.String(75), ForeignKey('user.id'))


class Repository(db.Model):
    """Class that represents the repository model"""

    id: Mapped[str] = mapped_column(db.String(75), primary_key=True)
    name: Mapped[str] = mapped_column(db.String(20), unique=True)
    description: Mapped[str] = mapped_column(db.String(100), nullable=True)
    user_id: Mapped[str] = mapped_column(db.String(75), ForeignKey('user.id'))


class User(db.Model, UserMixin):
    """Class that represents the user model"""

    id: Mapped[str] = mapped_column(db.String(75), primary_key=True)
    username: Mapped[str] = mapped_column(db.String(20), unique=True)
    password: Mapped[str] = mapped_column(db.String(20))

    repositories: Mapped[List[Repository]] = Relationship('Repository', backref="user")
    keys: Mapped[List[AuthenticationKey]] = Relationship('AuthenticationKey', backref="user")
