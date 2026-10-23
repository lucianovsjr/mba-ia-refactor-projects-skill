"""Acesso a dados das tabelas pedidos e itens_pedido."""

from src.utils.constants import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE

SELECT_PEDIDOS_COM_ITENS = """
    SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario,
           COALESCE(pr.nome, 'Desconhecido') AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""


def inserir(db, usuario_id, total):
    cursor = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, STATUS_PENDENTE, total),
    )
    return cursor.lastrowid


def inserir_item(db, pedido_id, produto_id, quantidade, preco_unitario):
    db.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def buscar_por_id(db, pedido_id):
    return db.execute(
        "SELECT id, usuario_id, status, total, criado_em FROM pedidos WHERE id = ?", (pedido_id,)
    ).fetchone()


def atualizar_status(db, pedido_id, status):
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))


def existe_item_com_produto(db, produto_id):
    return db.execute("SELECT 1 FROM itens_pedido WHERE produto_id = ? LIMIT 1", (produto_id,)).fetchone() is not None


def listar_com_itens(db, usuario_id=None):
    """Pedidos com seus itens em uma única query (JOIN), agrupados em memória."""
    sql, params = SELECT_PEDIDOS_COM_ITENS, []
    if usuario_id is not None:
        sql += " WHERE p.usuario_id = ?"
        params.append(usuario_id)
    sql += " ORDER BY p.id, i.id"

    pedidos = {}
    for row in db.execute(sql, params).fetchall():
        pedido = pedidos.setdefault(row["id"], {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        })
        if row["produto_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


def resumo_vendas(db):
    """Contagens e faturamento em uma única agregação."""
    return db.execute(
        """
        SELECT COUNT(*) AS total_pedidos,
               COALESCE(SUM(total), 0) AS faturamento,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,
               COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados
        FROM pedidos
        """,
        (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
    ).fetchone()


def contar(db):
    return db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
