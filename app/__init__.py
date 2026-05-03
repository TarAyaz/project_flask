from flask import Flask
from dotenv import load_dotenv
from app.main.routes import bp as main_bp
from app.auth.routes import auth_bp
from app.data import db_session
from app.data.models import User
from flask_login import LoginManager
from app.config import Config

load_dotenv()
login_manager = LoginManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db_session.global_init(app.config["DATABASE_PATH"])
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    return app


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(int(user_id))
