from flask import Blueprint

stash_api = Blueprint("stash_api", __name__)


@stash_api.route("/")
def hello_world():
    return "Hello World"
