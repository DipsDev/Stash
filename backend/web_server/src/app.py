import os

from flask import Flask, render_template
from flask_login import current_user

from blueprints.repos import repo
from services.database import db
from dotenv import load_dotenv
import backend.models as models
from blueprints.auth import auth
from services.login import login_manager

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

# Database related config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../../../db.sqlite'
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


app.register_blueprint(auth, url_prefix="/auth")
app.register_blueprint(repo, url_prefix="/")


@app.route("/")
def landing_page():
    """Main page"""
    user_repos = []
    new_repos = models.Repository.query.order_by(models.Repository.created_at.desc()).limit(10).all()
    if current_user.is_authenticated:
        user_repos = models.Repository.query.where(models.Repository.user_id == current_user.id).all()
    return render_template("main_page.html", repos=user_repos, new_repos=new_repos)


if __name__ == '__main__':
    app.run(debug=True)
