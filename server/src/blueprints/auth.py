"""
Module
"""
from flask import Blueprint, render_template, request, flash
import bcrypt
from sqlalchemy import select

from db.database import db
from db.models import User

auth = Blueprint("auth", __name__)

users = {
    1: {
        "username": "root",
        "password":  bcrypt.hashpw(b'root', bcrypt.gensalt()),
    }
}


@auth.route("/register", methods=['POST', 'GET'])
def register_user():
    """Route responsible for handling user register"""
    return render_template("auth/register.html")


@auth.route("/login", methods=['POST', 'GET'])
def login_user():
    """Route responsible for handling user login"""
    if request.method == "GET":
        return render_template("auth/login.html")

    password = request.form.get("password")
    username = request.form.get("username")

    if not password or not username:
        flash("Invalid credentials, please make sure the credentials are valid.")
        return render_template("auth/login.html")

    user = db.session.execute(select(User).where(User.username == username)).all()
    return user


