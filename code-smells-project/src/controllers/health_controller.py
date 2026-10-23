import logging
import sqlite3

from src.database.connection import get_db
from src.models import pedido_model, produto_model, usuario_model
from src.utils.constants import APP_VERSION

logger = logging.getLogger(__name__)


def health(ambiente):
    """Estado da aplicação, sem segredos nem caminhos internos."""
    try:
        db = get_db()
        counts = {
            "produtos": produto_model.contar(db),
            "usuarios": usuario_model.contar(db),
            "pedidos": pedido_model.contar(db),
        }
    except sqlite3.Error:
        logger.exception("Health check falhou")
        return {"status": "erro", "detalhes": "Banco de dados indisponível"}

    return {
        "status": "ok",
        "database": "connected",
        "counts": counts,
        "versao": APP_VERSION,
        "ambiente": ambiente,
    }
