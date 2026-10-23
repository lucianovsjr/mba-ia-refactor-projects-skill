"""Acesso a dados da tabela produtos."""

SELECT_PRODUTOS = "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos"


def listar(db):
    return db.execute(SELECT_PRODUTOS + " ORDER BY id").fetchall()


def buscar_por_id(db, produto_id):
    return db.execute(SELECT_PRODUTOS + " WHERE id = ?", (produto_id,)).fetchone()


def buscar_por_ids(db, produto_ids):
    """Retorna {id: row} para os ids informados, em uma única query."""
    ids = list(set(produto_ids))
    placeholders = ", ".join("?" for _ in ids)
    rows = db.execute(SELECT_PRODUTOS + " WHERE id IN (" + placeholders + ")", ids).fetchall()
    return {row["id"]: row for row in rows}


def buscar(db, termo=None, categoria=None, preco_min=None, preco_max=None):
    condicoes, params = [], []
    if termo:
        condicoes.append("(nome LIKE ? OR descricao LIKE ?)")
        padrao = f"%{termo}%"
        params += [padrao, padrao]
    if categoria:
        condicoes.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        condicoes.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        condicoes.append("preco <= ?")
        params.append(preco_max)

    sql = SELECT_PRODUTOS
    if condicoes:
        sql += " WHERE " + " AND ".join(condicoes)
    return db.execute(sql + " ORDER BY id", params).fetchall()


def inserir(db, nome, descricao, preco, estoque, categoria):
    cursor = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    return cursor.lastrowid


def atualizar(db, produto_id, nome, descricao, preco, estoque, categoria):
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )


def remover(db, produto_id):
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))


def baixar_estoque(db, produto_id, quantidade):
    """Decremento atômico: só baixa se houver estoque suficiente."""
    cursor = db.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
        (quantidade, produto_id, quantidade),
    )
    return cursor.rowcount == 1


def contar(db):
    return db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
