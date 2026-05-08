import os
import requests
import uuid
from asgiref.sync import sync_to_async
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
from app.forms.book import SearchForm, CreateBookForm
from app.forms.user import EditProfileForm
from app.utils.open_library_api import search_books
from app.data import db_session
from app.data.models import User, Book, SearchQuery
from app.utils.recommendations import get_recommendations

bp = Blueprint("main", __name__)


def save_picture(form_picture):
    rand_hex = uuid.uuid4().hex
    filename = secure_filename(form_picture.filename)
    _, f = os.path.splitext(filename)
    picture_fn = rand_hex + f
    picture_path = os.path.join(
        current_app.root_path, "static/images/profile_pics", picture_fn
    )
    form_picture.save(picture_path)
    return picture_fn


def save_book_cover(form_picture):
    rand_hex = uuid.uuid4().hex
    _, f = os.path.splitext(form_picture.filename)
    picture_fn = rand_hex + f
    upload_path = os.path.join(current_app.root_path, "static/images/book_covers")
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    picture_path = os.path.join(upload_path, picture_fn)
    form_picture.save(picture_path)
    return url_for("static", filename="images/book_covers/" + picture_fn)


def delete_file_safe(file_url, folder):
    if not file_url:
        return
    filename = file_url.split("/")[-1]
    if file_url.startswith("http") or filename == "plug.png":
        return

    file_path = os.path.join(current_app.root_path, "static/images", folder, filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Ошибка при удалении файла {filename}: {e}")


@bp.route("/profile", methods=["GET", "POST"])
@login_required
async def profile():
    form = EditProfileForm()
    db_sess = db_session.create_session()
    if form.validate_on_submit():

        def update_user():
            user = db_sess.query(User).filter(User.id == current_user.id).first()
            if form.avatar.data:
                old_avatar = user.avatar_file
                if old_avatar and old_avatar != "default_avatar.png":
                    old_path = os.path.join(
                        current_app.root_path, "static/images/profile_pics", old_avatar
                    )
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception as e:
                            print(f"Ошибка при удалении старого аватара: {e}")
                picture_file = save_picture(form.avatar.data)
                user.avatar_file = picture_file
            user.username = form.username.data
            db_sess.commit()

        await sync_to_async(update_user)()
        flash("Профиль успешно обновлен!", "success")
        return redirect(url_for("main.profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
    avatar_path = url_for(
        "static", filename="images/profile_pics/" + current_user.avatar_file
    )
    return render_template(
        "profile.html", title="Профиль", form=form, avatar_path=avatar_path
    )


@bp.route("/add_to_shelf", methods=["POST"])
@login_required
async def add_to_shelf():
    db_sess = db_session.create_session()
    data = {
        "title": request.form.get("title"),
        "author": request.form.get("author"),
        "isbn": request.form.get("isbn"),
        "genre": request.form.get("subject"),
        "cover_url": request.form.get("cover_url"),
        "status": request.form.get("status"),
        "query": request.form.get("last_search_query"),
    }

    def db_operation():
        existing_book = (
            db_sess.query(Book)
            .filter(
                Book.user_id == current_user.id,
                Book.title == data["title"],
                Book.author == data["author"],
            )
            .first()
        )
        if existing_book:
            return f"Книга '{data['title']}' уже есть на полке!", "info"
        else:
            new_book = Book(
                title=data["title"],
                author=data["author"],
                isbn=data["isbn"],
                genre=data["genre"],
                cover_url=data["cover_url"],
                status=data["status"],
                user_id=current_user.id,
            )
            db_sess.add(new_book)
            db_sess.commit()
            return (
                f"Книга '{data['title']}' добавлена в раздел '{data['status']}'!",
                "success",
            )

    msg, category = await sync_to_async(db_operation)()
    flash(msg, category)
    return redirect(url_for("main.search", q=data["query"]))


@bp.route("/")
async def index():
    db_sess = db_session.create_session()

    def get_data():
        user_books = []
        if current_user.is_authenticated:
            user_books = (
                db_sess.query(Book).filter(Book.user_id == current_user.id).all()
            )
        return get_recommendations(user_books)

    recommendations = await sync_to_async(get_data)()
    return render_template(
        "index.html", title="Добро пожаловать", recommendations=recommendations
    )


@bp.route("/search", methods=["GET", "POST"])
async def search():
    form = SearchForm()
    books = []
    recent_searches = []
    db_sess = db_session.create_session()
    if current_user.is_authenticated:

        def get_history():
            return (
                db_sess.query(SearchQuery.query)
                .filter(SearchQuery.user_id == current_user.id)
                .order_by(SearchQuery.timestamp.desc())
                .limit(10)
                .all()
            )

        hist = await sync_to_async(get_history)()
        seen = set()
        for s in hist:
            if s[0] not in seen:
                recent_searches.append(s[0])
                seen.add(s[0])
            if len(recent_searches) >= 6:
                break

    query_from_url = request.args.get("q")
    current_query = None

    if form.validate_on_submit():
        current_query = form.query.data
    elif query_from_url:
        form.query.data = query_from_url
        current_query = query_from_url

    if current_query:
        books = await sync_to_async(search_books)(current_query)
        if current_user.is_authenticated:

            def save_search_and_cleanup():
                search_entry = SearchQuery(query=current_query, user_id=current_user.id)
                db_sess.add(search_entry)
                db_sess.commit()
                MAX_HISTORY = 10
                old_queries = (
                    db_sess.query(SearchQuery.id)
                    .filter(SearchQuery.user_id == current_user.id)
                    .order_by(SearchQuery.timestamp.desc())
                    .offset(MAX_HISTORY)
                    .all()
                )
                if old_queries:
                    ids_to_delete = [q.id for q in old_queries]
                    db_sess.query(SearchQuery).filter(
                        SearchQuery.id.in_(ids_to_delete)
                    ).delete(synchronize_session=False)
                    db_sess.commit()

            await sync_to_async(save_search_and_cleanup)()

    return render_template(
        "search.html",
        title="Поиск",
        form=form,
        books=books,
        recent_searches=recent_searches,
    )


@bp.route("/my_shelf")
@login_required
async def my_shelf():
    db_sess = db_session.create_session()

    def get_books():
        return db_sess.query(Book).filter(Book.user_id == current_user.id).all()

    books = await sync_to_async(get_books)()
    shelf = {
        "reading": [b for b in books if b.status == "Читаю"],
        "plan": [b for b in books if b.status == "Хочу прочитать"],
        "completed": [b for b in books if b.status == "Прочитано"],
        "custom": [b for b in books if b.is_custom],
    }

    return render_template("my_shelf.html", title="Моя полка", shelf=shelf)


@bp.route("/delete_book/<int:book_id>", methods=["POST"])
@login_required
async def delete_book(book_id):
    db_sess = db_session.create_session()

    def do_delete():
        book = (
            db_sess.query(Book)
            .filter(Book.id == book_id, Book.user_id == current_user.id)
            .first()
        )
        if book:
            if book.is_custom:
                delete_file_safe(book.cover_url, "book_covers")
            db_sess.delete(book)
            db_sess.commit()
            return True
        return False

    if await sync_to_async(do_delete)():
        flash("Книга удалена с полки", "success")
    else:
        flash("Книга не найдена", "danger")

    return redirect(url_for("main.my_shelf"))


@bp.route("/update_book_status/<int:book_id>", methods=["POST"])
@login_required
async def update_book_status(book_id):
    db_sess = db_session.create_session()
    new_status = request.form.get("status")

    def do_update():
        book = (
            db_sess.query(Book)
            .filter(Book.id == book_id, Book.user_id == current_user.id)
            .first()
        )
        if book and new_status:
            book.status = new_status
            db_sess.commit()
            return book.title
        return None

    title = await sync_to_async(do_update)()
    if title:
        flash(f"Статус книги '{title}' изменен", "success")
    else:
        flash("Ошибка обновления статуса", "danger")

    return redirect(url_for("main.my_shelf"))


@bp.route("/book/<path:ol_id>")
async def book_details(ol_id):
    search_query = request.args.get("q", "")
    url = f"https://openlibrary.org/{ol_id}.json"

    def fetch_data():
        response = requests.get(url)
        return response.json()

    data = await sync_to_async(fetch_data)()
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


@bp.route("/create_book", methods=["GET", "POST"])
@login_required
async def create_book():
    form = CreateBookForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        cover_url = None
        if form.cover.data:
            cover_url = await sync_to_async(save_book_cover)(form.cover.data)
        new_book = Book(
            title=form.title.data,
            description=form.description.data,
            content=form.content.data,
            author=current_user.username,
            cover_url=cover_url,
            status="Собственная книга",
            is_custom=True,
            user_id=current_user.id,
        )

        def save():
            db_sess.add(new_book)
            db_sess.commit()

        await sync_to_async(save)()
        flash("Книга успешно создана!", "success")
        return redirect(url_for("main.my_shelf"))

    return render_template("create_book.html", form=form)


@bp.route("/read_my_book/<int:book_id>")
@login_required
async def read_my_book(book_id):
    db_sess = db_session.create_session()

    def get_book():
        return (
            db_sess.query(Book)
            .filter(Book.id == book_id, Book.user_id == current_user.id)
            .first()
        )

    book = await sync_to_async(get_book)()
    if not book or not book.is_custom:
        flash("Книга не найдена", "danger")
        return redirect(url_for("main.my_shelf"))
    return render_template("read_my_book.html", book=book)


@bp.route("/edit_book/<int:book_id>", methods=["GET", "POST"])
@login_required
async def edit_book(book_id):
    db_sess = db_session.create_session()

    def get_book():
        return (
            db_sess.query(Book)
            .filter(
                Book.id == book_id,
                Book.user_id == current_user.id,
                Book.is_custom == True,
            )
            .first()
        )

    book = await sync_to_async(get_book)()
    if not book:
        flash("Книга не найдена или её нельзя редактировать", "danger")
        return redirect(url_for("main.my_shelf"))
    form = CreateBookForm()
    if form.validate_on_submit():

        def update_logic():
            book.title = form.title.data
            book.description = form.description.data
            book.content = form.content.data
            if form.cover.data:
                delete_file_safe(book.cover_url, "book_covers")
                book.cover_url = save_book_cover(form.cover.data)

            db_sess.commit()

        await sync_to_async(update_logic)()
        flash("Изменения сохранены!", "success")
        return redirect(url_for("main.my_shelf"))
    elif request.method == "GET":
        form.title.data = book.title
        form.description.data = book.description
        form.content.data = book.content

    return render_template(
        "create_book.html", form=form, title="Редактирование", is_edit=True, book=book
    )
