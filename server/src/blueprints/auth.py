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


class LoginForm(FlaskForm):
    username = StringField("username", validators=[DataRequired("Username must have a value.")])
    password = StringField("password", validators=[DataRequired("Password must have a value.")])

    def validate_username(self, field):
        if db.session.execute(select(User).where(User.username == field.data)).one_or_none() is None:
            raise ValidationError("Username or password are invalid.")

    def validate_password(self, field):
        user = db.session.execute(select(User).where(User.username == field.data)).one_or_none()
        if not bcrypt.checkpw(bytes(field.data, encoding="utf-8"), user[0].password):
            raise ValidationError("Username or password are invalid.")


@auth.route("/login", methods=['POST', 'GET'])
def login_user():
    """Route responsible for handling user login"""
    form = LoginForm()

    if form.validate_on_submit():
        return redirect(url_for("landing_page"))

    return render_template("auth/login.html", form=form)
