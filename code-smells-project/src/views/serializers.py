"""Serialização por lista branca: só os campos listados chegam ao cliente."""

PRODUTO_FIELDS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")
USUARIO_FIELDS = ("id", "nome", "email", "tipo", "criado_em")
USUARIO_LOGIN_FIELDS = ("id", "nome", "email", "tipo")


def _pick(row, fields):
    return {field: row[field] for field in fields}


def produto_to_dict(row):
    return _pick(row, PRODUTO_FIELDS)


def usuario_to_dict(row):
    return _pick(row, USUARIO_FIELDS)


def usuario_login_to_dict(row):
    return _pick(row, USUARIO_LOGIN_FIELDS)
