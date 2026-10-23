from flask import Blueprint, jsonify, request

from controllers import user_controller
from routes.serializers import user_task_summary, user_with_task_count, user_with_tasks
from utils.dates import utcnow

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify([user_with_task_count(user, count) for user, count in user_controller.list_users()]), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = user_controller.get_user(user_id)
    return jsonify(user_with_tasks(user, user_controller.get_user_tasks(user_id))), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    user = user_controller.create_user(request.get_json(silent=True))
    return jsonify(user.to_dict()), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = user_controller.update_user(user_id, request.get_json(silent=True))
    return jsonify(user.to_dict()), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user_controller.delete_user(user_id)
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    now = utcnow()
    return jsonify([user_task_summary(task, now) for task in user_controller.get_user_tasks(user_id)]), 200


@user_bp.route('/login', methods=['POST'])
def login():
    user, token = user_controller.login(request.get_json(silent=True))
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': token,
    }), 200
