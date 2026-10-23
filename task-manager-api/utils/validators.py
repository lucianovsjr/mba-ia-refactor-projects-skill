"""Validação de entrada na borda. Cada função devolve só os campos aceitos, já convertidos."""
import re
from datetime import datetime

from models.task import Task
from utils.constants import (
    DATE_FORMAT,
    DEFAULT_COLOR,
    DEFAULT_PRIORITY,
    DEFAULT_TASK_STATUS,
    MAX_TITLE_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_TITLE_LENGTH,
)
from utils.errors import ValidationError

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9+_.-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")
COLOR_REGEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def require_json_object(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError("Dados inválidos")
    return data


def _optional_text(value, message):
    if value is not None and not isinstance(value, str):
        raise ValidationError(message)
    return value


def _optional_id(value, field):
    if value is not None and not _is_int(value):
        raise ValidationError(f"{field} inválido")
    return value


# ---------- tasks ----------

def _title(value):
    if not isinstance(value, str):
        raise ValidationError("Título é obrigatório")
    if len(value) < MIN_TITLE_LENGTH:
        raise ValidationError("Título muito curto")
    if len(value) > MAX_TITLE_LENGTH:
        raise ValidationError("Título muito longo")
    return value


def _status(value):
    if not Task.is_valid_status(value):
        raise ValidationError("Status inválido")
    return value


def _priority(value):
    if not _is_int(value) or not Task.is_valid_priority(value):
        raise ValidationError("Prioridade deve ser entre 1 e 5")
    return value


def _due_date(value, message):
    if not value:
        return None
    if not isinstance(value, str):
        raise ValidationError(message)
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        raise ValidationError(message) from None


def _tags(value):
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(tag, str) for tag in value):
        return ",".join(value)
    raise ValidationError("Tags inválidas")


def validate_task_create(data):
    data = require_json_object(data)
    if not data.get("title"):
        raise ValidationError("Título é obrigatório")
    return {
        "title": _title(data["title"]),
        "description": _optional_text(data.get("description", ""), "Descrição inválida"),
        "status": _status(data.get("status", DEFAULT_TASK_STATUS)),
        "priority": _priority(data.get("priority", DEFAULT_PRIORITY)),
        "user_id": _optional_id(data.get("user_id"), "user_id") or None,
        "category_id": _optional_id(data.get("category_id"), "category_id") or None,
        "due_date": _due_date(data.get("due_date"), "Formato de data inválido. Use YYYY-MM-DD"),
        "tags": _tags(data.get("tags")) or None,
    }


def validate_task_update(data):
    data = require_json_object(data)
    fields = {}
    if "title" in data:
        fields["title"] = _title(data["title"])
    if "description" in data:
        fields["description"] = _optional_text(data["description"], "Descrição inválida")
    if "status" in data:
        fields["status"] = _status(data["status"])
    if "priority" in data:
        fields["priority"] = _priority(data["priority"])
    if "user_id" in data:
        fields["user_id"] = _optional_id(data["user_id"], "user_id") or None
    if "category_id" in data:
        fields["category_id"] = _optional_id(data["category_id"], "category_id") or None
    if "due_date" in data:
        fields["due_date"] = _due_date(data["due_date"], "Formato de data inválido")
    if "tags" in data:
        fields["tags"] = _tags(data["tags"])
    return fields


def validate_task_search(args):
    filters = {"text": args.get("q", ""), "status": args.get("status", "")}
    for field, message in (("priority", "Prioridade inválida"), ("user_id", "user_id inválido")):
        raw = args.get(field, "")
        if raw:
            try:
                filters[field] = int(raw)
            except ValueError:
                raise ValidationError(message) from None
    return filters


# ---------- users ----------

def _email(value):
    if not isinstance(value, str) or not EMAIL_REGEX.match(value):
        raise ValidationError("Email inválido")
    return value


def validate_user_create(data):
    data = require_json_object(data)
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    if not name or not isinstance(name, str):
        raise ValidationError("Nome é obrigatório")
    if not email:
        raise ValidationError("Email é obrigatório")
    if not password or not isinstance(password, str):
        raise ValidationError("Senha é obrigatória")
    _email(email)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError("Senha deve ter no mínimo 4 caracteres")
    # role/active do body são ignorados: o papel não é definido pelo próprio cliente (bloqueio de escalada)
    return {"name": name, "email": email, "password": password}


def validate_user_update(data):
    data = require_json_object(data)
    fields = {}
    if "name" in data:
        if not data["name"] or not isinstance(data["name"], str):
            raise ValidationError("Nome é obrigatório")
        fields["name"] = data["name"]
    if "email" in data:
        fields["email"] = _email(data["email"])
    if "password" in data:
        password = data["password"]
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError("Senha muito curta")
        fields["password"] = password
    return fields


def validate_login(data):
    data = require_json_object(data)
    email, password = data.get("email"), data.get("password")
    if not email or not password or not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError("Email e senha são obrigatórios")
    return email, password


# ---------- categories ----------

def _color(value):
    if not isinstance(value, str) or not COLOR_REGEX.match(value):
        raise ValidationError("Cor inválida")
    return value


def _category_name(value):
    if not value or not isinstance(value, str):
        raise ValidationError("Nome é obrigatório")
    return value


def validate_category_create(data):
    data = require_json_object(data)
    return {
        "name": _category_name(data.get("name")),
        "description": _optional_text(data.get("description", ""), "Descrição inválida"),
        "color": _color(data.get("color", DEFAULT_COLOR)),
    }


def validate_category_update(data):
    data = require_json_object(data)
    fields = {}
    if "name" in data:
        fields["name"] = _category_name(data["name"])
    if "description" in data:
        fields["description"] = _optional_text(data["description"], "Descrição inválida")
    if "color" in data:
        fields["color"] = _color(data["color"])
    return fields
