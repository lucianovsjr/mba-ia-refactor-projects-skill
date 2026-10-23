from flask import Blueprint, jsonify, request

from controllers import category_controller
from routes.serializers import category_with_task_count

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = category_controller.list_categories()
    return jsonify([category_with_task_count(category, count) for category, count in categories]), 200


@category_bp.route('/categories', methods=['POST'])
def create_category():
    category = category_controller.create_category(request.get_json(silent=True))
    return jsonify(category.to_dict()), 201


@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    category = category_controller.update_category(category_id, request.get_json(silent=True))
    return jsonify(category.to_dict()), 200


@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    category_controller.delete_category(category_id)
    return jsonify({'message': 'Categoria deletada'}), 200
