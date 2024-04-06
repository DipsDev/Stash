from datetime import datetime
from typing import List

from flask_login import UserMixin
from sqlalchemy.orm import Relationship, mapped_column, Mapped
from sqlalchemy import ForeignKey
from services.database import db


class Repository(db.Model):
    """Class that represents the repository model"""

    id: Mapped[str] = mapped_column(db.String(75), primary_key=True)
    name: Mapped[str] = mapped_column(db.String(20), unique=True)
    description: Mapped[str] = mapped_column(db.String(100), nullable=True)
    user_id: Mapped[str] = mapped_column(db.String(75), ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)


class PullRequest(db.model):
    """Class that represents a pull request"""
    id: Mapped[str] = mapped_column(db.String(75), primary_key=True)
    repo_id: Mapped[str] = mapped_column(db.String(75), ForeignKey("repository.id"))
    author_id: Mapped[str] = mapped_column(db.String(75), ForeignKey('user.id'))
    description: Mapped[str] = mapped_column(db.String(125), nullable=True)
    head_hash: Mapped[str] = mapped_column(db.String(40), nullable=False, unique=True)


class User(db.Model, UserMixin):
    """Class that represents the user model"""

    id: Mapped[str] = mapped_column(db.String(75), primary_key=True)
    username: Mapped[str] = mapped_column(db.String(20), unique=True)
    password: Mapped[str] = mapped_column(db.String(20))

    repositories: Mapped[List[Repository]] = Relationship('Repository', backref="user")
