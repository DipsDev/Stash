"""
Module that handles all api related actions
"""
import os
from functools import wraps

from flask import Blueprint, abort, request

from services.models import Repository, User, AuthenticationKey

from services.file_system import file_system

stash_api = Blueprint("stash_api", __name__)


def is_directory_traversal(file_name):
    current_directory = os.path.abspath(os.curdir)
    requested_path = os.path.relpath(file_name, start=current_directory)
    requested_path = os.path.abspath(requested_path)
    common_prefix = os.path.commonprefix([requested_path, current_directory])
    return common_prefix != current_directory


def uses_repository(url: str, methods=None):
    if methods is None:
        methods = ['GET']

    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            auth_token = request.headers.get('Authorization')
            if not auth_token:
                return abort(401)
            auth_token = auth_token.lstrip("Bearer ")
            authenticated_key = AuthenticationKey.query.where(AuthenticationKey.value == auth_token).first()
            if authenticated_key is None:
                return abort(401)

            repo_name = kwargs.get("repo_name")
            kwargs.pop("repo_name")

            current_repo = Repository.query.join(User).where(Repository.name == repo_name).first_or_404()
            if current_repo.user.id != authenticated_key.user_id:
                return abort(401)

            return func(*args, **kwargs, repo=current_repo)

        route_url = f"<repo_name>.stash/{url.lstrip('/')}"

        stash_api.add_url_rule(route_url, view_func=decorated_function, methods=methods)
        return decorated_function

    return decorator


@uses_repository('/<branch>/head')
def current_head_commit(repo, branch):
    """Get the current head commit"""
    head_cmt = file_system.get_head_commit(repo.id, branch)
    if head_cmt is None:
        abort(404)
    return head_cmt


@uses_repository("/objects/<s>/<c>")
def get_server_object(repo: Repository, s: str, c: str):
    """Fetch an object from the web_server"""
    if len(s) != 2 or len(c) != 38:
        abort(400)
    obj = file_system.get_server_object(repo.id, s, c)
    if obj is None:
        abort(404)
    return obj
