import hmac
from functools import wraps

from flask import current_app, request

from src.utils.errors import ForbiddenError, NotFoundError


def admin_required(view):
    """Rotas administrativas: desligadas por padrão; quando ligadas, exigem X-Admin-Token."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_app.config["ENABLE_ADMIN_ENDPOINTS"]:
            raise NotFoundError("Rota não encontrada", com_sucesso=True)
        esperado = current_app.config["ADMIN_TOKEN"]
        recebido = request.headers.get("X-Admin-Token", "")
        if not esperado or not hmac.compare_digest(recebido, esperado):
            raise ForbiddenError("Acesso negado", com_sucesso=True)
        return view(*args, **kwargs)

    return wrapper
