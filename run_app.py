from app import create_app
from app.data import db_session

app = create_app()
app.config["SECRET_KEY"] = "yandexlyceum_secret_key"
db_session.global_init("db/library.db")

if __name__ == "__main__":
    app.run(debug=True)
