import logging

from src.database.connection import get_db
from src.database.schema import limpar_tabelas

logger = logging.getLogger(__name__)


def reset_database():
    db = get_db()
    with db:
        limpar_tabelas(db)
    logger.warning("Banco de dados resetado via endpoint administrativo")
