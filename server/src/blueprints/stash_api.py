"""
Module that handles all api related actions
"""
from functools import wraps

from flask import Blueprint
from flask_login import current_user

from db.login import login_manager
from db.models import Repository, User

stash_api = Blueprint("stash_api", __name__)


def uses_repository(url: str, methods=None):
    if methods is None:
        methods = ['GET']

    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):

            if not current_user.is_authenticated:
                return login_manager.unauthorized()

            repo_name = kwargs.get("repo_name")

            current_repo = Repository.query.join(User).where(Repository.name == repo_name).first_or_404()
            if current_repo.user.id != current_user.id:
                return login_manager.unauthorized()

            return func(*args, repo=current_repo)

        route_url = f"<repo_name>.stash/{url}"

        stash_api.add_url_rule(route_url, view_func=decorated_function, methods=methods)
        return decorated_function

    return decorator


@uses_repository('test')
def current_head_commit(repo):
    return repo.id
