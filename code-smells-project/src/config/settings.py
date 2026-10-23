import os
import secrets


def _bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _list(value):
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    """Configuração lida do ambiente. Os defaults servem só para desenvolvimento."""

    def __init__(self, environ=None):
        env = os.environ if environ is None else environ
        self.SECRET_KEY = env.get("SECRET_KEY") or secrets.token_hex(32)
        self.DEBUG = _bool(env.get("FLASK_DEBUG"), default=False)
        self.HOST = env.get("HOST", "127.0.0.1")
        self.PORT = int(env.get("PORT", "5000"))
        self.APP_ENV = env.get("APP_ENV", "development")
        self.DATABASE_PATH = env.get("DATABASE_PATH", "loja.db")
        self.CORS_ORIGINS = _list(env.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"))
        self.LOG_LEVEL = env.get("LOG_LEVEL", "INFO").upper()
        self.ENABLE_ADMIN_ENDPOINTS = _bool(env.get("ENABLE_ADMIN_ENDPOINTS"), default=False)
        self.ADMIN_TOKEN = env.get("ADMIN_TOKEN", "")
