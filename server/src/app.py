import os

from flask import Flask, render_template
from flask_login import current_user
from sqlalchemy import Join, select

from db.database import db
from dotenv import load_dotenv
import db.models as models
from blueprints.auth import auth
from blueprints.stash_api import stash_api
from db.login import login_manager

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

# Database related config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
db.init_app(app)
with app.app_context():
    db.create_all()

# Auth related config
login_manager.init_app(app)
login_manager.login_view = "auth.login_route"


@login_manager.user_loader
def load_user(user_id):
    user = models.User.query.filter_by(id=user_id).first()
    return user


# Routes related config
app.register_blueprint(stash_api, url_prefix="/stash")
app.register_blueprint(auth, url_prefix="/auth")


@app.route("/")
def landing_page():
    """Main page"""
    user_repos = []
    if current_user.is_authenticated:
        user_repos = db.session.execute(select(models.User)
                                        .where(models.User.id == current_user.id).join(models.Repository)).all()
    return render_template("main_page.html", repos=user_repos)


if __name__ == '__main__':
    app.run()
