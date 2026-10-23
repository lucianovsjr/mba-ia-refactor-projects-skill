"""Notificações de pedido. Hoje só registram em log; o ponto de integração (e-mail, SMS, push) fica aqui."""

import logging

logger = logging.getLogger(__name__)


def pedido_criado(pedido_id, usuario_id):
    logger.info("Notificação (email/sms/push): pedido_id=%s criado para usuario_id=%s", pedido_id, usuario_id)


def pedido_aprovado(pedido_id):
    logger.info("Notificação: pedido_id=%s aprovado, preparar envio", pedido_id)


def pedido_cancelado(pedido_id):
    logger.info("Notificação: pedido_id=%s cancelado, verificar devolução de estoque", pedido_id)
