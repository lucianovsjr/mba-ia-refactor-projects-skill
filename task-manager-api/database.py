from contextlib import contextmanager

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


@contextmanager
def transaction():
    """Uma unidade de trabalho: commit no sucesso, rollback em qualquer exceção."""
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
