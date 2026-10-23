"""Formatos de resposta compostos (View). Os campos base vêm do to_dict() de cada model."""
from utils.dates import utcnow


def task_with_overdue(task, now=None):
    data = task.to_dict()
    data['overdue'] = task.is_overdue(now or utcnow())
    return data


def task_list_item(task, now):
    data = task_with_overdue(task, now)
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def user_task_summary(task, now):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': str(task.created_at),
        'due_date': str(task.due_date) if task.due_date else None,
        'overdue': task.is_overdue(now),
    }


def user_with_task_count(user, task_count):
    data = user.to_dict()
    data['task_count'] = task_count
    return data


def user_with_tasks(user, tasks):
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in tasks]
    return data


def category_with_task_count(category, task_count):
    data = category.to_dict()
    data['task_count'] = task_count
    return data
