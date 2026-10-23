from flask import Blueprint, jsonify

from src.controllers import admin_controller
from src.middlewares.auth import admin_required

admin_bp = Blueprint("admin", __name__)

# O antigo POST /admin/query (execução de SQL arbitrário) foi removido.


@admin_bp.route("/admin/reset-db", methods=["POST"])
@admin_required
def reset_database():
    admin_controller.reset_database()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
