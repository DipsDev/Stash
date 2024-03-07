from typing import List

from flask_login import UserMixin
from sqlalchemy.orm import Relationship, mapped_column, Mapped
from sqlalchemy import ForeignKey
from .database import db


class Repository(db.Model):
    """Class that represents the repository model"""

    id: Mapped[str] = mapped_column(db.String(75), primary_key=True)
    name: Mapped[str] = mapped_column(db.String(20), unique=True)
    user_id: Mapped[str] = mapped_column(db.String(75), ForeignKey('user.id'))


class User(db.Model, UserMixin):
    """Class that represents the user model"""

    id: Mapped[str] = mapped_column(db.String(75), primary_key=True)
    username: Mapped[str] = mapped_column(db.String(20), unique=True)
    password: Mapped[str] = mapped_column(db.String(20))
    repositories: Mapped[List[Repository]] = Relationship('Repository', backref="user")
