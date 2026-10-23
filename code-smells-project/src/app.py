import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings
from src.database import connection
from src.middlewares.error_handler import register_error_handlers
from src.views.admin_routes import admin_bp
from src.views.pedido_routes import pedido_bp
from src.views.produto_routes import produto_bp
from src.views.relatorio_routes import relatorio_bp
from src.views.system_routes import system_bp
from src.views.usuario_routes import usuario_bp

BLUEPRINTS = (system_bp, produto_bp, usuario_bp, pedido_bp, relatorio_bp, admin_bp)


def create_app(config=None):
    """Composition root: config, logging, CORS, banco, error handlers e rotas."""
    config = config or Settings()

    logging.basicConfig(level=config.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app, origins=config.CORS_ORIGINS)

    connection.init_app(app)
    register_error_handlers(app)
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

    return app
