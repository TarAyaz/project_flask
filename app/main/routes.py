from flask import Blueprint, render_template
from app.forms.book import SearchForm
from app.utils.open_library_api import search_books


bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html", title="Добро пожаловать")


@bp.route("/search", methods=["GET", "POST"])
def search():
    form = SearchForm()
    books = []
    if form.validate_on_submit():
        books = search_books(form.query.data)
    return render_template("search.html", title="Главная", form=form, books=books)
