from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed


class SearchForm(FlaskForm):
    query = StringField("Название книги или автор", validators=[DataRequired()])
    submit = SubmitField("Найти")


class CreateBookForm(FlaskForm):
    title = StringField(
        "Название Произведения", validators=[DataRequired(), Length(min=2, max=50)]
    )
    description = StringField(
        "Краткая аннотация", validators=[DataRequired(), Length(max=150)]
    )
    content = TextAreaField("Текст книги", validators=[DataRequired()])
    cover = FileField(
        "Обложка книги",
        validators=[
            FileAllowed(["jpg", "png", "jpeg"], "Только изображения"),
        ],
    )
    submit = SubmitField("Опубликовать книгу")
