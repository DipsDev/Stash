from flask import Flask, render_template

from .blueprints.auth import auth
from .blueprints.stash_api import stash_api

app = Flask(__name__)

app.secret_key = "62tTuCMjXgCkPjw/B2AzvWLDe5Dz8UnonnD0TQnHG9jDxybe4Loo6uHz/jEckm/O"

app.register_blueprint(stash_api, url_prefix="/stash")
app.register_blueprint(auth, url_prefix="/auth")


@app.route("/")
def landing_page():
    """Main page"""
    return render_template("main_page.html")


if __name__ == '__main__':
    app.run()
