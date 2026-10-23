import logging

from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

DDL = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)

PRODUTOS_SEED = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

# Senhas de exemplo para desenvolvimento; gravadas apenas como hash.
USUARIOS_SEED = [
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
]

PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def init_db(db):
    with db:
        for statement in DDL:
            db.execute(statement)
        _seed_if_empty(db)
        _migrar_senhas_legadas(db)


def _seed_if_empty(db):
    if db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        return
    db.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        PRODUTOS_SEED,
    )
    db.executemany(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        [(nome, email, generate_password_hash(senha), tipo) for nome, email, senha, tipo in USUARIOS_SEED],
    )
    logger.info("Banco populado com dados de exemplo")


def _migrar_senhas_legadas(db):
    """Converte senhas em texto puro de bancos criados pela versão antiga."""
    legadas = [
        row for row in db.execute("SELECT id, senha FROM usuarios").fetchall()
        if row["senha"] and not row["senha"].startswith(PREFIXOS_HASH)
    ]
    for row in legadas:
        db.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (generate_password_hash(row["senha"]), row["id"]))
    if legadas:
        logger.warning("%d senha(s) em texto puro convertidas para hash", len(legadas))


def limpar_tabelas(db):
    for statement in (
        "DELETE FROM itens_pedido",
        "DELETE FROM pedidos",
        "DELETE FROM produtos",
        "DELETE FROM usuarios",
    ):
        db.execute(statement)
