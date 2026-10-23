import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.utils.errors import AppError

logger = logging.getLogger(__name__)

MENSAGENS_HTTP = {
    404: "Rota não encontrada",
    405: "Método não permitido",
}


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        corpo = {"erro": err.message}
        if err.com_sucesso:
            corpo["sucesso"] = False
        return jsonify(corpo), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        mensagem = MENSAGENS_HTTP.get(err.code, err.name)
        return jsonify({"erro": mensagem, "sucesso": False}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro inesperado")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
