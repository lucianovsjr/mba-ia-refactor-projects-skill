from sqlalchemy import func
from sqlalchemy.orm import joinedload

from database import db
from utils.constants import (
    CLOSED_TASK_STATUSES,
    DEFAULT_PRIORITY,
    DEFAULT_TASK_STATUS,
    DONE_STATUS,
    MAX_PRIORITY,
    MIN_PRIORITY,
    TASK_STATUSES,
)
from utils.dates import utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_TASK_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    # ---------- regras de domínio ----------

    @staticmethod
    def is_valid_status(status):
        return status in TASK_STATUSES

    @staticmethod
    def is_valid_priority(priority):
        return MIN_PRIORITY <= priority <= MAX_PRIORITY

    def is_overdue(self, now=None):
        now = now or utcnow()
        return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_TASK_STATUSES

    @staticmethod
    def completion_rate(done, total):
        return round((done / total) * 100, 2) if total > 0 else 0

    @classmethod
    def overdue_clause(cls, now):
        """Mesma regra de is_overdue(), como condição SQL."""
        return db.and_(cls.due_date.is_not(None), cls.due_date < now, cls.status.not_in(CLOSED_TASK_STATUSES))

    # ---------- acesso a dados ----------

    @classmethod
    def get(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_with_relations(cls):
        query = db.select(cls).options(joinedload(cls.user), joinedload(cls.category)).order_by(cls.id)
        return db.session.execute(query).scalars().all()

    @classmethod
    def list_by_user(cls, user_id):
        return db.session.execute(db.select(cls).filter_by(user_id=user_id).order_by(cls.id)).scalars().all()

    @classmethod
    def search(cls, text='', status='', priority=None, user_id=None):
        query = db.select(cls)
        if text:
            pattern = f'%{text}%'
            query = query.where(db.or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            query = query.where(cls.status == status)
        if priority is not None:
            query = query.where(cls.priority == priority)
        if user_id is not None:
            query = query.where(cls.user_id == user_id)
        return db.session.execute(query.order_by(cls.id)).scalars().all()

    @classmethod
    def list_overdue(cls, now):
        return db.session.execute(db.select(cls).where(cls.overdue_clause(now)).order_by(cls.id)).scalars().all()

    @classmethod
    def count(cls, *conditions):
        return db.session.scalar(db.select(func.count(cls.id)).where(*conditions))

    @classmethod
    def count_by(cls, column):
        """{valor da coluna: quantidade} numa única query com GROUP BY."""
        return dict(db.session.execute(db.select(column, func.count(cls.id)).group_by(column)).all())

    @classmethod
    def stats_by_user(cls):
        """{user_id: (total, concluídas)} numa única query."""
        done = func.sum(db.case((cls.status == DONE_STATUS, 1), else_=0))
        rows = db.session.execute(
            db.select(cls.user_id, func.count(cls.id), done).where(cls.user_id.is_not(None)).group_by(cls.user_id)
        ).all()
        return {user_id: (total, completed or 0) for user_id, total, completed in rows}

    @classmethod
    def unassign_category(cls, category_id):
        db.session.execute(db.update(cls).where(cls.category_id == category_id).values(category_id=None))
