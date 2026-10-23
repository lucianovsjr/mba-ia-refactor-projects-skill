from datetime import timedelta

from controllers.user_controller import get_user
from models.category import Category
from models.task import Task
from models.user import User
from utils.constants import DONE_STATUS, HIGH_PRIORITY_MAX, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, TASK_STATUSES
from utils.dates import utcnow


def summary_report():
    now = utcnow()
    since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

    by_status = Task.count_by(Task.status)
    by_priority = Task.count_by(Task.priority)
    overdue_tasks = Task.list_overdue(now)
    stats_by_user = Task.stats_by_user()

    user_productivity = []
    for user in User.list_all():
        total, completed = stats_by_user.get(user.id, (0, 0))
        user_productivity.append({
            "user_id": user.id,
            "user_name": user.name,
            "total_tasks": total,
            "completed_tasks": completed,
            "completion_rate": Task.completion_rate(completed, total),
        })

    return {
        "generated_at": str(now),
        "overview": {
            "total_tasks": Task.count(),
            "total_users": User.count(),
            "total_categories": Category.count(),
        },
        "tasks_by_status": {status: by_status.get(status, 0) for status in TASK_STATUSES},
        "tasks_by_priority": {label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()},
        "overdue": {
            "count": len(overdue_tasks),
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "due_date": str(task.due_date),
                    "days_overdue": (now - task.due_date).days,
                }
                for task in overdue_tasks
            ],
        },
        "recent_activity": {
            "tasks_created_last_7_days": Task.count(Task.created_at >= since),
            "tasks_completed_last_7_days": Task.count(Task.status == DONE_STATUS, Task.updated_at >= since),
        },
        "user_productivity": user_productivity,
    }


def user_report(user_id):
    user = get_user(user_id)
    tasks = Task.list_by_user(user_id)
    now = utcnow()

    by_status = {status: 0 for status in TASK_STATUSES}
    for task in tasks:
        if task.status in by_status:
            by_status[task.status] += 1
    done = by_status[DONE_STATUS]

    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": {
            "total_tasks": len(tasks),
            **by_status,
            "overdue": sum(1 for task in tasks if task.is_overdue(now)),
            "high_priority": sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
            "completion_rate": Task.completion_rate(done, len(tasks)),
        },
    }
