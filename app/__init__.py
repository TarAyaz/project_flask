from flask import Flask
from app.main.routes import bp as main_bp
from app.auth.routes import auth_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    return app
