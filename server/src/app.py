from flask import Flask, render_template

from .blueprints.auth import auth
from .blueprints.stash_api import stash_api

app = Flask(__name__)

app.register_blueprint(stash_api, url_prefix="/stash")
app.register_blueprint(auth, url_prefix="/auth")


@app.route("/")
def landing_page():
    return render_template("main_page.html")


if __name__ == '__main__':
    app.run()
