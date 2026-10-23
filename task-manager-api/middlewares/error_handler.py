import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.errors import AppError

logger = logging.getLogger(__name__)

HTTP_MESSAGES = {
    404: "Rota não encontrada",
    405: "Método não permitido",
}


def register_error_handlers(app):
    """Todas as respostas de erro saem como {'error': mensagem}, o formato já usado pela API."""

    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"error": err.message}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify({"error": HTTP_MESSAGES.get(err.code, err.name)}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro inesperado")
        return jsonify({"error": "Erro interno"}), 500
