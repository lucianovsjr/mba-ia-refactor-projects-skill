from flask import Blueprint, jsonify, request

from src.controllers import usuario_controller
from src.views.serializers import usuario_login_to_dict, usuario_to_dict

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    usuarios = usuario_controller.listar_usuarios()
    return jsonify({"dados": [usuario_to_dict(u) for u in usuarios], "sucesso": True}), 200


@usuario_bp.route("/usuarios/<int:usuario_id>", methods=["GET"])
def buscar_usuario(usuario_id):
    usuario = usuario_controller.buscar_usuario(usuario_id)
    return jsonify({"dados": usuario_to_dict(usuario), "sucesso": True}), 200


@usuario_bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    usuario_id = usuario_controller.criar_usuario(request.get_json(silent=True))
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


@usuario_bp.route("/login", methods=["POST"])
def login():
    usuario = usuario_controller.login(request.get_json(silent=True))
    return jsonify({"dados": usuario_login_to_dict(usuario), "sucesso": True, "mensagem": "Login OK"}), 200
