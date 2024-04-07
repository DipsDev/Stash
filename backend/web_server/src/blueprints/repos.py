"""
Module that handles creating, viewing and editing repositories
"""
import hashlib

from flask import Blueprint, render_template, redirect, url_for, abort
from flask_wtf import FlaskForm
from sqlalchemy import select
from wtforms import StringField, RadioField, ValidationError
from wtforms.validators import DataRequired, Optional
from flask_login import login_required, current_user
import re

from services.database import db
from backend.models import Repository, User, PullRequest
from services.file_system import file_system

repo = Blueprint("repo", __name__)


class CreateRepositoryForm(FlaskForm):
    repository_name = StringField('repository_name', validators=[DataRequired("Repository name should have a value.")])
    description = StringField('description', validators=[Optional(True)])

    initial_value = RadioField('initial_value',
                               choices=[("empty", "empty repo"), ("clone", "clone a repo"),
                                        ("readme", "create a repo with a default readme.md")],
                               validators=[DataRequired()])

    source_id = StringField('source_id')

    def validate_repository_name(self, field):
        exist_repo = db.session.execute(select(Repository).where(Repository.name == field.data,
                                                                 Repository.user_id == current_user.id)).one_or_none()
        if exist_repo:
            raise ValidationError("Repository name is already in use. Please choose another.")
        if not re.compile(r'^[A-Za-z0-9_.-]+$').match(field.data):
            raise ValidationError("Repository name cannot contain spaces and special characters (other then a '-').")

    def validate_source_id(self, field):
        if self.initial_value.data != "clone":
            return

        if not field.data:
            raise ValidationError("You must provide a source id in order to create a clone.")

        repo_sourced_id = db.session.execute(select(Repository).where(Repository.id == field.data)).one_or_none()
        if repo_sourced_id is None:
            raise ValidationError("You must provide a valid source id.")


@repo.route("/new", methods=['POST', 'GET'])
@login_required
def new():
    """Route responsible for rendering the repo creation page"""
    form = CreateRepositoryForm()
    if form.validate_on_submit():
        created_repo_id = hashlib.sha1(f"{form.repository_name.data[:40]}_{current_user.username[:20]}_repository".encode()).hexdigest()
        created_repo = Repository(id=created_repo_id, name=form.repository_name.data,
                                  description=form.description.data, user_id=current_user.id)

        db.session.add(created_repo)
        db.session.commit()
        file_system.allocate_repository(created_repo_id)
        return redirect(url_for(".view_repo", username=current_user.username, repo_name=form.repository_name.data))
    return render_template("repo/new.html", form=form)


@repo.route("/<username>/<repo_name>/fork", methods=['POST'])
@login_required
def fork(username: str, repo_name: str):
    """Route for forking an existing repository"""
    current_repo = Repository.query.where(Repository.name == repo_name).first_or_404()
    new_id = hashlib.sha1(f"{current_repo.id}_fork_{current_user.username[:10]}".encode()).hexdigest()

    created_repo = Repository(id=new_id, name=f"fork_{repo_name}_{current_user.username}",
                              description=f"Fork of {username}/{repo_name}", user_id=current_user.id)
    db.session.add(created_repo)
    db.session.commit()
    file_system.allocate_repository(new_id)
    return redirect(url_for(".view_repo", username=current_user.username,
                            repo_name=f"fork_{repo_name}_{current_user.username}"))


@repo.route("/<username>/<repo_name>/pulls")
def pulls(username: str, repo_name: str):
    """Route for viewing the pull requests"""
    repo_owner = User.query.where(User.username == username).first_or_404()
    current_repo = Repository.query.where(Repository.name == repo_name, Repository.user_id == repo_owner.id).first_or_404()
    pull_requests = PullRequest.query.join(User).where(PullRequest.repo_id == current_repo.id).all()
    return render_template("repo/pulls.html", repo=current_repo, prs=pull_requests)


@repo.route("/<username>/<repo_name>/")
def view_repo(username: str, repo_name: str):
    """Route responsible for viewing a user's repo"""
    repo_owner = User.query.where(User.username == username).first_or_404()
    current_repo = Repository.query.join(User).where(Repository.name == repo_name, Repository.user_id == repo_owner.id).first_or_404()
    data = file_system.get_current_commit_files(current_repo.id, "main")
    message, files = "", []
    if len(data) > 0:
        message, files = data
    head_commit = file_system.get_head_commit(current_repo.id, "main")
    return render_template("repo/view.html", repo=current_repo, files=files,
                           last_commit=head_commit, commit_message=message)


@repo.route("/<username>/<repo_name>/<path:path>")
def view_repo_contents(username: str, repo_name: str, path: str):
    """Route responsible for viewing a user's repo contents"""
    repo_owner = User.query.where(User.username == username).first_or_404()
    current_repo = Repository.query.join(User).where(Repository.name == repo_name, Repository.user_id == repo_owner.id).first_or_404()
    d = file_system.get_nested_tree_contents(current_repo.id, path)
    if d is None:
        abort(404)
    tp, data = d

    if tp == "tree":
        return render_template("repo/view.html", repo=current_repo, files=data, commit_message="", last_commit="")
    else:
        file_content = file_system.get_server_object(current_repo.id, data[:2], data[2:])
        if file_content is None:
            abort(404)
        try:
            content = file_content.decode().split("\n")
            valid_encoding = True
        except UnicodeDecodeError:
            content = []
            valid_encoding = False
        return render_template("repo/view_file.html", repo=current_repo, path=path,
                               file_content=enumerate(content), commit_message="", last_commit="",
                               valid_encoding=valid_encoding)
