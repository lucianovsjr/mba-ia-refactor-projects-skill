from flask import Blueprint, current_app, jsonify

from src.controllers import health_controller
from src.utils.constants import APP_VERSION

system_bp = Blueprint("system", __name__)


@system_bp.route("/", methods=["GET"])
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": APP_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


@system_bp.route("/health", methods=["GET"])
def health_check():
    estado = health_controller.health(ambiente=current_app.config["APP_ENV"])
    return jsonify(estado), 200 if estado["status"] == "ok" else 500
