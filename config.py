import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
PORT = int(os.environ.get("PORT", "5000"))
DB_PATH = os.environ.get("DB_PATH", "db/notes.sqlite")
