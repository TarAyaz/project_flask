import os
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from flask_login import login_required, current_user
from app.forms.book import SearchForm
from app.forms.user import EditProfileForm
from app.utils.open_library_api import search_books
from app.data import db_session
from app.data.models import User

bp = Blueprint("main", __name__)


def save_picture(form_picture):
    picture_fn = form_picture.filename
    picture_path = os.path.join(
        current_app.root_path, "static/profile_pics", picture_fn
    )
    form_picture.save(picture_path)
    return picture_fn


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = EditProfileForm()
    db_sess = db_session.create_session()
    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        if form.avatar.data:
            picture_file = save_picture(form.avatar.data)
            user.avatar_file = picture_file
        user.username = form.username.data
        db_sess.commit()
        flash("Профиль успешно обновлен!", "success")
        return redirect(url_for("main.profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
    avatar_path = url_for("static", filename="profile_pics/" + current_user.avatar_file)
    return render_template(
        "profile.html", title="Профиль", form=form, avatar_path=avatar_path
    )


@bp.route("/")
def index():
    return render_template("index.html", title="Добро пожаловать")


@bp.route("/search", methods=["GET", "POST"])
def search():
    form = SearchForm()
    books = []
    if form.validate_on_submit():
        books = search_books(form.query.data)
    return render_template("search.html", title="Поиск", form=form, books=books)
