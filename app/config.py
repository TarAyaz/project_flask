import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-key"
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or "sqlite:///db/library.db"
    )
    DATABASE_PATH = SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "")
    FERNET_KEY = os.environ.get("FERNET_KEY")
