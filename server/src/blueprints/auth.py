"""
Module that handles register and login
"""

from flask import Blueprint, render_template, redirect, url_for
import bcrypt
from flask_login import login_user, logout_user
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
def register_route():
    """Route responsible for handling user register"""

    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.hashpw(bytes(form.password.data, encoding="utf-8"), bcrypt.gensalt())
        new_id = str(uuid.uuid4())
        new_user = User(username=form.username.data, password=hashed_password, id=new_id)  # type: ignore[call-arg]
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for(".login_route"))

    return render_template("auth/register.html", form=form)


class LoginForm(FlaskForm):
    username = StringField("username", validators=[DataRequired("Username must have a value.")])
    password = StringField("password", validators=[DataRequired("Password must have a value.")])

    def __init__(self, *k, **kwargs):
        super(LoginForm, self).__init__(*k, **kwargs)
        self._mem_user = None

    def validate(self, extra_validators=None):
        self._mem_user = db.session.execute(select(User).where(User.username == self.username.data)).one_or_none()
        return super(LoginForm, self).validate()

    def validate_password(self, field):
        if not self._mem_user or not bcrypt.checkpw(bytes(field.data, encoding="utf-8"), self._mem_user[0].password):
            raise ValidationError("Username or password are invalid.")


@auth.route("/login", methods=['POST', 'GET'])
def login_route():
    """Route responsible for handling user login"""
    form = LoginForm()

    if form.validate_on_submit():
        user = db.session.execute(select(User).where(User.username == form.username.data)).first()[0]
        login_user(user)
        return redirect(url_for("landing_page"))

    return render_template("auth/login.html", form=form)


@auth.route("/logout")
def logout_route():
    """Logout user from the current session"""
    logout_user()
    return redirect(url_for(".login_route"))
