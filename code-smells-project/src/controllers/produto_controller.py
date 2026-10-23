import logging

from src.database.connection import get_db
from src.models import pedido_model, produto_model
from src.utils.errors import ConflictError, NotFoundError
from src.utils.validators import parse_preco_opcional, validar_produto

logger = logging.getLogger(__name__)


def listar_produtos():
    return produto_model.listar(get_db())


def buscar_produto(produto_id):
    produto = produto_model.buscar_por_id(get_db(), produto_id)
    if produto is None:
        raise NotFoundError("Produto não encontrado", com_sucesso=True)
    return produto


def buscar_produtos(termo, categoria, preco_min, preco_max):
    return produto_model.buscar(
        get_db(),
        termo=termo,
        categoria=categoria,
        preco_min=parse_preco_opcional(preco_min, "preco_min"),
        preco_max=parse_preco_opcional(preco_max, "preco_max"),
    )


def criar_produto(dados):
    campos = validar_produto(dados)
    db = get_db()
    with db:
        produto_id = produto_model.inserir(db, **campos)
    logger.info("Produto criado id=%s", produto_id)
    return produto_id


def atualizar_produto(produto_id, dados):
    db = get_db()
    if produto_model.buscar_por_id(db, produto_id) is None:
        raise NotFoundError("Produto não encontrado")
    campos = validar_produto(dados)
    with db:
        produto_model.atualizar(db, produto_id, **campos)


def deletar_produto(produto_id):
    db = get_db()
    if produto_model.buscar_por_id(db, produto_id) is None:
        raise NotFoundError("Produto não encontrado")
    if pedido_model.existe_item_com_produto(db, produto_id):
        raise ConflictError("Produto possui pedidos e não pode ser removido")
    with db:
        produto_model.remover(db, produto_id)
    logger.info("Produto removido id=%s", produto_id)
