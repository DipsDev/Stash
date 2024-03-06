import os

from flask import Flask, render_template
from db.database import db
from dotenv import load_dotenv
import db.models as models
from blueprints.auth import auth
from blueprints.stash_api import stash_api


load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

# Database related config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

# Routes related config
app.register_blueprint(stash_api, url_prefix="/stash")
app.register_blueprint(auth, url_prefix="/auth")
db.init_app(app)
with app.app_context():
    db.create_all()


@app.route("/")
def landing_page():
    """Main page"""
    return render_template("main_page.html")


if __name__ == '__main__':
    app.run()
