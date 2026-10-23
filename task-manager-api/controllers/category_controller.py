import logging

from database import transaction
from models.category import Category
from models.task import Task
from utils.errors import NotFoundError
from utils.validators import validate_category_create, validate_category_update

logger = logging.getLogger(__name__)


def list_categories():
    return Category.list_with_task_count()


def get_category(category_id):
    category = Category.get(category_id)
    if category is None:
        raise NotFoundError("Categoria não encontrada")
    return category


def create_category(data):
    category = Category(**validate_category_create(data))
    with transaction() as session:
        session.add(category)
    logger.info("Categoria criada id=%s", category.id)
    return category


def update_category(category_id, data):
    category = get_category(category_id)
    fields = validate_category_update(data)
    with transaction():
        for name, value in fields.items():
            setattr(category, name, value)
    return category


def delete_category(category_id):
    category = get_category(category_id)
    with transaction() as session:
        # As tasks da categoria ficam sem categoria, na mesma transação da exclusão
        Task.unassign_category(category_id)
        session.delete(category)
    logger.info("Categoria deletada id=%s", category_id)
