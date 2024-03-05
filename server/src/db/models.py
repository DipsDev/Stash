from typing import List

from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey
from .database import db


class Repository(db.Model):
    """Class that represents the repository model"""
    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))


class User(db.Model):
    """Class that represents the user model"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column()

    repositories: Mapped[List[Repository]] = relationship()
