from app import create_app

app = create_app()
app.config["SECRET_KEY"] = "yandexlyceum_secret_key"

if __name__ == "__main__":
    app.run(debug=True)
