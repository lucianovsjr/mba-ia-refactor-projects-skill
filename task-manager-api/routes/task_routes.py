from flask import Blueprint, jsonify, request

from controllers import task_controller
from routes.serializers import task_list_item, task_with_overdue
from utils.dates import utcnow

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    now = utcnow()
    return jsonify([task_list_item(task, now) for task in task_controller.list_tasks()]), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    return jsonify(task_with_overdue(task_controller.get_task(task_id))), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    task = task_controller.create_task(request.get_json(silent=True))
    return jsonify(task.to_dict()), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = task_controller.update_task(task_id, request.get_json(silent=True))
    return jsonify(task.to_dict()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task_controller.delete_task(task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    return jsonify([task.to_dict() for task in task_controller.search_tasks(request.args)]), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_controller.task_stats()), 200
