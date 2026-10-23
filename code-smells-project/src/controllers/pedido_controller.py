from src.database.connection import get_db
from src.models import pedido_model, produto_model, usuario_model
from src.services import notification_service
from src.utils.constants import STATUS_APROVADO, STATUS_CANCELADO
from src.utils.errors import BusinessRuleError, NotFoundError
from src.utils.validators import validar_pedido, validar_status


def criar_pedido(dados):
    pedido = validar_pedido(dados)
    usuario_id, itens = pedido["usuario_id"], pedido["itens"]
    db = get_db()

    if usuario_model.buscar_por_id(db, usuario_id) is None:
        raise NotFoundError("Usuário não encontrado", com_sucesso=True)

    produtos = produto_model.buscar_por_ids(db, [item["produto_id"] for item in itens])
    total = 0
    for item in itens:
        produto = produtos.get(item["produto_id"])
        if produto is None:
            raise BusinessRuleError(f"Produto {item['produto_id']} não encontrado", com_sucesso=True)
        if produto["estoque"] < item["quantidade"]:
            raise BusinessRuleError(f"Estoque insuficiente para {produto['nome']}", com_sucesso=True)
        total = total + produto["preco"] * item["quantidade"]

    with db:  # commit no sucesso, rollback em qualquer exceção
        pedido_id = pedido_model.inserir(db, usuario_id, total)
        for item in itens:
            produto = produtos[item["produto_id"]]
            pedido_model.inserir_item(db, pedido_id, item["produto_id"], item["quantidade"], produto["preco"])
            if not produto_model.baixar_estoque(db, item["produto_id"], item["quantidade"]):
                raise BusinessRuleError(f"Estoque insuficiente para {produto['nome']}", com_sucesso=True)

    notification_service.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def listar_pedidos(usuario_id=None):
    return pedido_model.listar_com_itens(get_db(), usuario_id)


def atualizar_status_pedido(pedido_id, dados):
    novo_status = validar_status(dados)
    db = get_db()
    if pedido_model.buscar_por_id(db, pedido_id) is None:
        raise NotFoundError("Pedido não encontrado")
    with db:
        pedido_model.atualizar_status(db, pedido_id, novo_status)

    if novo_status == STATUS_APROVADO:
        notification_service.pedido_aprovado(pedido_id)
    elif novo_status == STATUS_CANCELADO:
        notification_service.pedido_cancelado(pedido_id)
