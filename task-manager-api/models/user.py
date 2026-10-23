import hashlib
import hmac
import re

from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models.task import Task
from utils.constants import DEFAULT_ROLE
from utils.dates import utcnow

LEGACY_MD5_HASH = re.compile(r'^[0-9a-f]{32}$')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        """Lista branca de campos públicos: o hash da senha nunca sai na resposta."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    # ---------- senha ----------

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        if self.has_legacy_password_hash():
            legacy = hashlib.md5(password.encode()).hexdigest()
            return hmac.compare_digest(self.password, legacy)
        return check_password_hash(self.password, password)

    def has_legacy_password_hash(self):
        """Hashes MD5 gravados antes da refatoração; são regravados no próximo login válido."""
        return bool(LEGACY_MD5_HASH.match(self.password or ''))

    # ---------- acesso a dados ----------

    @classmethod
    def get(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def find_by_email(cls, email):
        return db.session.execute(db.select(cls).filter_by(email=email)).scalar_one_or_none()

    @classmethod
    def list_all(cls):
        return db.session.execute(db.select(cls).order_by(cls.id)).scalars().all()

    @classmethod
    def list_with_task_count(cls):
        """[(user, quantidade de tasks)] numa única query."""
        query = (
            db.select(cls, func.count(Task.id))
            .outerjoin(Task, Task.user_id == cls.id)
            .group_by(cls.id)
            .order_by(cls.id)
        )
        return db.session.execute(query).all()

    @classmethod
    def count(cls):
        return db.session.scalar(db.select(func.count(cls.id)))
