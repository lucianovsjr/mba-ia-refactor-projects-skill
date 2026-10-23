import re

from src.utils.constants import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
    STATUS_PEDIDO,
)
from src.utils.errors import ValidationError

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def require_json_object(dados):
    if not isinstance(dados, dict) or not dados:
        raise ValidationError("Dados inválidos")
    return dados


def validar_produto(dados):
    """Validação única para criar e atualizar produto."""
    dados = require_json_object(dados)
    for campo, mensagem in (
        ("nome", "Nome é obrigatório"),
        ("preco", "Preço é obrigatório"),
        ("estoque", "Estoque é obrigatório"),
    ):
        if campo not in dados:
            raise ValidationError(mensagem)

    nome = dados["nome"]
    descricao = dados.get("descricao") or ""
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome é obrigatório")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição inválida")
    if not _is_number(preco):
        raise ValidationError("Preço deve ser um número")
    if not _is_int(estoque):
        raise ValidationError("Estoque deve ser um número inteiro")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def parse_preco_opcional(valor, campo):
    if valor is None or valor == "":
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(f"{campo} inválido") from None


def validar_usuario(dados):
    dados = require_json_object(dados)
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not all(isinstance(valor, str) and valor for valor in (nome, email, senha)):
        raise ValidationError("Nome, email e senha são obrigatórios")
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Email inválido")
    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    dados = dados if isinstance(dados, dict) else {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not (isinstance(email, str) and email and isinstance(senha, str) and senha):
        raise ValidationError("Email e senha são obrigatórios")
    return email, senha


def validar_pedido(dados):
    dados = require_json_object(dados)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not _is_int(usuario_id):
        raise ValidationError("Usuario ID inválido")
    if not isinstance(itens, list) or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    for item in itens:
        if not isinstance(item, dict) or not _is_int(item.get("produto_id")) or not _is_int(item.get("quantidade")):
            raise ValidationError("Item inválido: produto_id e quantidade são obrigatórios")
        if item["quantidade"] <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")

    return {"usuario_id": usuario_id, "itens": [
        {"produto_id": item["produto_id"], "quantidade": item["quantidade"]} for item in itens
    ]}


def validar_status(dados):
    novo_status = dados.get("status", "") if isinstance(dados, dict) else ""
    if novo_status not in STATUS_PEDIDO:
        raise ValidationError("Status inválido")
    return novo_status
