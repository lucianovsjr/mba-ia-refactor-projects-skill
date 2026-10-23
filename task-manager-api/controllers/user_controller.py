import logging

from database import transaction
from models.task import Task
from models.user import User
from utils.constants import DEFAULT_ROLE, LOGIN_TOKEN_PREFIX
from utils.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from utils.validators import validate_login, validate_user_create, validate_user_update

logger = logging.getLogger(__name__)


def list_users():
    return User.list_with_task_count()


def get_user(user_id):
    user = User.get(user_id)
    if user is None:
        raise NotFoundError("Usuário não encontrado")
    return user


def get_user_tasks(user_id):
    get_user(user_id)
    return Task.list_by_user(user_id)


def create_user(data):
    fields = validate_user_create(data)
    if User.find_by_email(fields["email"]):
        raise ConflictError("Email já cadastrado")
    # O papel nunca vem do cliente numa rota pública: todo cadastro nasce com o papel padrão
    user = User(name=fields["name"], email=fields["email"], role=DEFAULT_ROLE)
    user.set_password(fields["password"])
    with transaction() as session:
        session.add(user)
    logger.info("Usuário criado id=%s", user.id)
    return user


def update_user(user_id, data):
    user = get_user(user_id)
    fields = validate_user_update(data)
    if "email" in fields:
        existing = User.find_by_email(fields["email"])
        if existing and existing.id != user_id:
            raise ConflictError("Email já cadastrado")
    with transaction():
        if "name" in fields:
            user.name = fields["name"]
        if "email" in fields:
            user.email = fields["email"]
        if "password" in fields:
            user.set_password(fields["password"])
    return user


def delete_user(user_id):
    user = get_user(user_id)
    with transaction() as session:
        for task in Task.list_by_user(user_id):
            session.delete(task)
        session.delete(user)
    logger.info("Usuário deletado id=%s", user_id)


def login(data):
    email, password = validate_login(data)
    user = User.find_by_email(email)
    if user is None or not user.check_password(password):
        raise UnauthorizedError("Credenciais inválidas")
    if not user.active:
        raise ForbiddenError("Usuário inativo")
    if user.has_legacy_password_hash():
        with transaction():
            user.set_password(password)
        logger.info("Hash de senha legado regravado id=%s", user.id)
    return user, LOGIN_TOKEN_PREFIX + str(user.id)
