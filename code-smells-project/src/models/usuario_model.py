"""Acesso a dados da tabela usuarios."""

SELECT_USUARIOS = "SELECT id, nome, email, senha, tipo, criado_em FROM usuarios"


def listar(db):
    return db.execute(SELECT_USUARIOS + " ORDER BY id").fetchall()


def buscar_por_id(db, usuario_id):
    return db.execute(SELECT_USUARIOS + " WHERE id = ?", (usuario_id,)).fetchone()


def buscar_por_email(db, email):
    return db.execute(SELECT_USUARIOS + " WHERE email = ? ORDER BY id LIMIT 1", (email,)).fetchone()


def inserir(db, nome, email, senha_hash, tipo):
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    return cursor.lastrowid


def contar(db):
    return db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
