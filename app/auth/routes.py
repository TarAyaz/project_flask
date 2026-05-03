from flask import Blueprint, render_template, redirect
from flask_login import login_user, logout_user, login_required
from app.forms.user import RegisterForm, LoginForm
from app.data import db_session
from app.data.models import User
from asgiref.sync import sync_to_async

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
async def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()

        def auth_logic():
            user = (
                db_sess.query(User).filter(User.username == form.username.data).first()
            )
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return True
            return False

        if await sync_to_async(auth_logic)():
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
async def logout():
    await sync_to_async(logout_user)()
    return redirect("/")


@auth_bp.route("/register", methods=["GET", "POST"])
async def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()

        def registration_logic():
            if db_sess.query(User).filter(User.email == form.email.data).first():
                return "Пользователь с такой почтой уже есть"
            if db_sess.query(User).filter(User.username == form.username.data).first():
                return "Такой логин уже занят"
            user = User(
                username=form.username.data,
                email=form.email.data,
            )
            user.password = form.password.data
            db_sess.add(user)
            db_sess.commit()
            return None

        error_message = await sync_to_async(registration_logic)()
        if error_message:
            return render_template(
                "register.html",
                title="Регистрация",
                form=form,
                message=error_message,
            )
        return redirect("/login")
    return render_template("register.html", title="Регистрация", form=form)
