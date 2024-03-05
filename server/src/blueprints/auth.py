"""
Module
"""
from flask import Blueprint, render_template, session, request
import bcrypt

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

    if bcrypt.checkpw(bytes(request.form.get("password"), encoding="utf-8"), users.get(1).get("password")):
        return "OK"
    return "NOT REQUESTED"

