"""
Module
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
import bcrypt
from sqlalchemy import select
import uuid
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, EqualTo, ValidationError

from db.database import db
from db.models import User

auth = Blueprint("auth", __name__)


class RegisterForm(FlaskForm):
    username = StringField('username', validators=[DataRequired("Username should have a value.")])
    password = StringField('password', validators=[DataRequired("Password should have a value.")])
    rep_password = StringField('rep_password',
                               validators=[DataRequired("Repeated password should have a value."),
                                           EqualTo("password", "Passwords must match.")])

    def validate_username(self, field):
        user_exists = db.session.execute(select(User).where(User.username == field.data)). \
            scalar_one_or_none()
        if user_exists:
            raise ValidationError("Username or password are invalid.")


@auth.route("/register", methods=['POST', 'GET'])
def register_user():
    """Route responsible for handling user register"""

    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.hashpw(bytes(form.password.data, encoding="utf-8"), bcrypt.gensalt())
        new_user = User(username=form.username.data, password=hashed_password, id=str(uuid.uuid4()))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for(".login_user"))

    return render_template("auth/register.html", form=form)


@auth.route("/login", methods=['POST', 'GET'])
def login_user():
    """Route responsible for handling user login"""
    if request.method == "GET":
        return render_template("auth/login.html")

    password = request.form.get("password")
    username = request.form.get("username")

    if not password or not username:
        flash("Invalid credentials, please make sure all credentials are valid.")
        return render_template("auth/login.html")

    user = db.session.execute(select(User).where(User.username == username)).one_or_none()
    if user is None:
        flash("Username or password are invalid.")
        return render_template("auth/login.html")

    print(user)
    is_same = bcrypt.checkpw(bytes(password, encoding="utf-8"), user[0].password)
    if not is_same:
        flash("Username or pasword are invalid.")
        return render_template("auth/login.html")

    return redirect(url_for("landing_page"))
