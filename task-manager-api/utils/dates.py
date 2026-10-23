from datetime import datetime, timezone


def utcnow():
    """UTC naive, compatível com as colunas DateTime sem timezone já gravadas."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
