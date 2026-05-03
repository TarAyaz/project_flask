import os
import requests
import uuid
from werkzeug.utils import secure_filename
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
from app.data.models import User, Book

bp = Blueprint("main", __name__)


def save_picture(form_picture):
    rand_hex = uuid.uuid4().hex
    filename = secure_filename(form_picture.filename)
    _, f = os.path.splitext(filename)
    picture_fn = rand_hex + f
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


@bp.route("/add_to_shelf", methods=["POST"])
@login_required
def add_to_shelf():
    db_sess = db_session.create_session()
    title = request.form.get("title")
    author = request.form.get("author")
    isbn = request.form.get("isbn")
    cover_url = request.form.get("cover_url")
    status = request.form.get("status")
    query = request.form.get("last_search_query")
    existing_book = (
        db_sess.query(Book)
        .filter(
            Book.user_id == current_user.id, Book.title == title, Book.author == author
        )
        .first()
    )
    if existing_book:
        flash(f"Книга '{title}' уже есть на полке!", "info")
    else:
        new_book = Book(
            title=title,
            author=author,
            isbn=isbn,
            cover_url=cover_url,
            status=status,
            user_id=current_user.id,
        )
        db_sess.add(new_book)
        db_sess.commit()
        flash(f"Книга '{title}' добавлена в раздел '{status}'!", "success")

    return redirect(url_for("main.search", q=query))


@bp.route("/")
def index():
    return render_template("index.html", title="Добро пожаловать")


@bp.route("/search", methods=["GET", "POST"])
def search():
    form = SearchForm()
    books = []
    query_from_url = request.args.get("q")
    if form.validate_on_submit():
        books = search_books(form.query.data)
    elif query_from_url:
        form.query.data = query_from_url
        books = search_books(query_from_url)
    return render_template("search.html", title="Поиск", form=form, books=books)


@bp.route("/my_shelf")
@login_required
def my_shelf():
    db_sess = db_session.create_session()
    books = db_sess.query(Book).filter(Book.user_id == current_user.id).all()
    shelf = {
        "reading": [b for b in books if b.status == "Читаю"],
        "plan": [b for b in books if b.status == "Хочу прочитать"],
        "completed": [b for b in books if b.status == "Прочитано"],
    }

    return render_template("my_shelf.html", title="Моя полка", shelf=shelf)


@bp.route("/delete_book/<int:book_id>", methods=["POST"])
@login_required
def delete_book(book_id):
    db_sess = db_session.create_session()

    book = (
        db_sess.query(Book)
        .filter(Book.id == book_id, Book.user_id == current_user.id)
        .first()
    )
    if book:
        db_sess.delete(book)
        db_sess.commit()
        flash("Книга удалена с полки", "success")
    else:
        flash("Книга не найдена", "danger")

    return redirect(url_for("main.my_shelf"))


@bp.route("/update_book_status/<int:book_id>", methods=["POST"])
@login_required
def update_book_status(book_id):
    db_sess = db_session.create_session()
    book = (
        db_sess.query(Book)
        .filter(Book.id == book_id, Book.user_id == current_user.id)
        .first()
    )

    new_status = request.form.get("status")
    if book and new_status:
        book.status = new_status
        db_sess.commit()
        flash(f"Статус книги '{book.title}' изменен", "success")

    return redirect(url_for("main.my_shelf"))


@bp.route("/book/<path:ol_id>")
def book_details(ol_id):
    search_query = request.args.get("q", "")
    url = f"https://openlibrary.org/{ol_id}.json"
    response = requests.get(url)
    data = response.json()
    description = data.get("description", "Описание отсутствует")
    if isinstance(description, dict):
        description = description.get("value")

    book = {
        "title": data.get("title"),
        "description": description,
        "subjects": data.get("subjects", [])[:10],
        "covers": data.get("covers", []),
    }

    cover_url = None
    if book["covers"]:
        cover_url = f"https://covers.openlibrary.org/b/id/{book['covers'][0]}-L.jpg"

    return render_template(
        "book_details.html",
        title=book["title"],
        book=book,
        cover_url=cover_url,
        search_query=search_query,
    )
