from flask import Flask, render_template
from .blueprints.stash_api import stash_api

app = Flask(__name__)

app.register_blueprint(stash_api, url_prefix="/stash")


@app.route("/")
def hello_world():
    return render_template("main_page.html")


if __name__ == '__main__':
    app.run()

