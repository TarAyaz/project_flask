import os
from flask import Flask
from dotenv import load_dotenv
from app.main.routes import bp as main_bp
from app.auth.routes import auth_bp
from app.data import db_session
from app.data.models import User
from flask_login import LoginManager

load_dotenv()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or "dev-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        os.environ.get("DATABASE_URL") or "sqlite:///db/library.db"
    )
    app.config["FERNET_KEY"] = os.environ.get("FERNET_KEY")

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    return app


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)
