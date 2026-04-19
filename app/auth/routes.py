from flask import Blueprint, render_template, redirect
from flask_login import login_user, logout_user, login_required
from app.forms.user import RegisterForm, LoginForm
from app.data import db_session
from app.data.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.username == form.username.data).first()
        if user and user.hashed_password == form.password.data:
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template(
            "login.html",
            title="Авторизация",
            form=form,
            message="Неверный логин или пароль",
        )
    return render_template("login.html", title="Авторизация", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template(
                "register.html",
                title="Регистрация",
                form=form,
                message="Пользователь с такой почтой уже есть",
            )
        if db_sess.query(User).filter(User.username == form.username.data).first():
            return render_template(
                "register.html",
                title="Регистрация",
                form=form,
                message="Такой логин уже занят",
            )

        user = User(
            username=form.username.data,
            email=form.email.data,
            hashed_password=form.password.data,
        )
        db_sess.add(user)
        db_sess.commit()
        return redirect("/login")
    return render_template("register.html", title="Регистрация", form=form)
