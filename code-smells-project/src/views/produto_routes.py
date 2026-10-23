from flask import Blueprint, jsonify, request

from src.controllers import produto_controller
from src.views.serializers import produto_to_dict

produto_bp = Blueprint("produtos", __name__)


@produto_bp.route("/produtos", methods=["GET"])
def listar_produtos():
    produtos = produto_controller.listar_produtos()
    return jsonify({"dados": [produto_to_dict(p) for p in produtos], "sucesso": True}), 200


@produto_bp.route("/produtos/busca", methods=["GET"])
def buscar_produtos():
    resultados = produto_controller.buscar_produtos(
        termo=request.args.get("q", ""),
        categoria=request.args.get("categoria"),
        preco_min=request.args.get("preco_min"),
        preco_max=request.args.get("preco_max"),
    )
    dados = [produto_to_dict(p) for p in resultados]
    return jsonify({"dados": dados, "total": len(dados), "sucesso": True}), 200


@produto_bp.route("/produtos/<int:produto_id>", methods=["GET"])
def buscar_produto(produto_id):
    produto = produto_controller.buscar_produto(produto_id)
    return jsonify({"dados": produto_to_dict(produto), "sucesso": True}), 200


@produto_bp.route("/produtos", methods=["POST"])
def criar_produto():
    produto_id = produto_controller.criar_produto(request.get_json(silent=True))
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


@produto_bp.route("/produtos/<int:produto_id>", methods=["PUT"])
def atualizar_produto(produto_id):
    produto_controller.atualizar_produto(produto_id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


@produto_bp.route("/produtos/<int:produto_id>", methods=["DELETE"])
def deletar_produto(produto_id):
    produto_controller.deletar_produto(produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
