import datetime
import sqlalchemy
from app.utils.crypto import CryptoManager
from sqlalchemy import orm
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = "users"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    email = sqlalchemy.Column(
        sqlalchemy.String, index=True, unique=True, nullable=False
    )
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    avatar_file = sqlalchemy.Column(sqlalchemy.String, default="default_avatar.png")
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    books = orm.relationship("Book", back_populates="user", lazy="subquery")
    searches = orm.relationship("SearchQuery", back_populates="user", lazy="subquery")

    @property
    def password(self):
        if self.hashed_password:
            return CryptoManager.decrypt(self.hashed_password)
        return None

    @password.setter
    def password(self, value):
        if value:
            self.hashed_password = CryptoManager.encrypt(value)
        else:
            self.hashed_password = None

    def check_password(self, password):
        return self.password == password


class Book(SqlAlchemyBase):
    __tablename__ = "books"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    author = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    isbn = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    genre = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    language = sqlalchemy.Column(sqlalchemy.String, default="ru")
    cover_url = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    status = sqlalchemy.Column(sqlalchemy.String, default="Хочу прочитать")
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship("User", back_populates="books")


class SearchQuery(SqlAlchemyBase):
    __tablename__ = "search_history"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    query = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    user = orm.relationship("User", back_populates="searches")
