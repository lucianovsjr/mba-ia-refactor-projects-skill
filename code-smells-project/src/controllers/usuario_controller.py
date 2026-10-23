import logging

from werkzeug.security import check_password_hash, generate_password_hash

from src.database.connection import get_db
from src.models import usuario_model
from src.utils.constants import TIPO_USUARIO_PADRAO
from src.utils.errors import ConflictError, NotFoundError, UnauthorizedError
from src.utils.validators import validar_login, validar_usuario

logger = logging.getLogger(__name__)


def listar_usuarios():
    return usuario_model.listar(get_db())


def buscar_usuario(usuario_id):
    usuario = usuario_model.buscar_por_id(get_db(), usuario_id)
    if usuario is None:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar_usuario(dados):
    campos = validar_usuario(dados)
    db = get_db()
    if usuario_model.buscar_por_email(db, campos["email"]) is not None:
        raise ConflictError("Email já cadastrado")
    with db:
        # O tipo nunca vem do body: cadastro público sempre cria cliente.
        usuario_id = usuario_model.inserir(
            db, campos["nome"], campos["email"], generate_password_hash(campos["senha"]), TIPO_USUARIO_PADRAO
        )
    logger.info("Usuário criado id=%s", usuario_id)
    return usuario_id


def login(dados):
    email, senha = validar_login(dados)
    usuario = usuario_model.buscar_por_email(get_db(), email)
    if usuario is None or not check_password_hash(usuario["senha"], senha):
        logger.warning("Falha de login")
        raise UnauthorizedError("Email ou senha inválidos", com_sucesso=True)
    logger.info("Login bem-sucedido usuario_id=%s", usuario["id"])
    return usuario
