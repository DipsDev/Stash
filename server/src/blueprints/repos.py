"""
Module that handles creating, viewing and editing repositories
"""
from flask import Blueprint, render_template
from flask_wtf import FlaskForm
from sqlalchemy import select
from wtforms import StringField, RadioField, ValidationError
from wtforms.validators import DataRequired, Length, Optional
import re

from db.database import db
from db.models import Repository

repo = Blueprint("repo", __name__)


class CreateRepositoryForm(FlaskForm):
    repository_name = StringField('repository_name', validators=[DataRequired("Repository name should have a value."),
                                                                 Length(3, 12,
                                                                        "Repository name must be between 3-12 "
                                                                        "characters.")])
    description = StringField('description', validators=[Optional(True)])

    initial_value = RadioField('initial_value',
                               choices=[("empty", "empty repo"), ("clone", "clone a repo"),
                                        ("readme", "create a repo with a default readme.md")],
                               validators=[DataRequired()])

    source_id = StringField('source_id')

    def validate_repository_name(self, field):
        exist_repo = db.session.execute(select(Repository).where(Repository.name == field.data)).one_or_none()
        if exist_repo:
            raise ValidationError("Repository name is already in use. Please choose another.")
        if not re.compile(r'^[A-Za-z0-9_.-]+$').match(field.data):
            raise ValidationError("Invalid repository name was chosen. Please use another one.")

    def validate_source_id(self, field):
        if self.initial_value.data != "clone":
            return

        if not field.data:
            raise ValidationError("You must provide a source id in order to create a clone.")

        repo_sourced_id = db.session.execute(select(Repository).where(Repository.id == field.data)).one_or_none()
        if repo_sourced_id is None:
            raise ValidationError("You must provide a valid source id.")


@repo.route("/new", methods=['POST', 'GET'])
def new():
    """Route responsible for rendering the repo creation page"""
    form = CreateRepositoryForm()
    if form.validate_on_submit():
        return render_template("landing_page")
    return render_template("repo/new.html", form=form)
