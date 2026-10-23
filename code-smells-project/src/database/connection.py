import sqlite3

from flask import current_app, g

from src.database import schema


def connect(database_path):
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    """Conexão da requisição atual (uma por app context, fechada no teardown)."""
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_PATH"])
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        schema.init_db(get_db())
