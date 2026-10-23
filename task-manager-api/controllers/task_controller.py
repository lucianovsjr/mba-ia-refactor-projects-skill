import logging

from database import transaction
from models.category import Category
from models.task import Task
from models.user import User
from utils.constants import DONE_STATUS, TASK_STATUSES
from utils.dates import utcnow
from utils.errors import NotFoundError
from utils.validators import validate_task_create, validate_task_search, validate_task_update

logger = logging.getLogger(__name__)


def _ensure_references(fields):
    if fields.get("user_id") and User.get(fields["user_id"]) is None:
        raise NotFoundError("Usuário não encontrado")
    if fields.get("category_id") and Category.get(fields["category_id"]) is None:
        raise NotFoundError("Categoria não encontrada")


def list_tasks():
    return Task.list_with_relations()


def get_task(task_id):
    task = Task.get(task_id)
    if task is None:
        raise NotFoundError("Task não encontrada")
    return task


def create_task(data):
    fields = validate_task_create(data)
    _ensure_references(fields)
    task = Task(**fields)
    with transaction() as session:
        session.add(task)
    logger.info("Task criada id=%s", task.id)
    return task


def update_task(task_id, data):
    task = get_task(task_id)
    fields = validate_task_update(data)
    _ensure_references(fields)
    with transaction():
        for name, value in fields.items():
            setattr(task, name, value)
        task.updated_at = utcnow()
    logger.info("Task atualizada id=%s", task.id)
    return task


def delete_task(task_id):
    task = get_task(task_id)
    with transaction() as session:
        session.delete(task)
    logger.info("Task deletada id=%s", task_id)


def search_tasks(args):
    return Task.search(**validate_task_search(args))


def task_stats():
    total = Task.count()
    by_status = Task.count_by(Task.status)
    done = by_status.get(DONE_STATUS, 0)
    stats = {status: by_status.get(status, 0) for status in TASK_STATUSES}
    stats.update({
        "total": total,
        "overdue": Task.count(Task.overdue_clause(utcnow())),
        "completion_rate": Task.completion_rate(done, total),
    })
    return stats
