const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../utils/constants');

const maskCard = (cardNumber) => `**** **** **** ${cardNumber.slice(-4)}`;

// Gateway simulado: aprova cartões com o prefixo configurado
function createPaymentService({ logger }) {
    return {
        charge(cardNumber, amount) {
            logger.info(`Processando pagamento de ${amount} com cartão ${maskCard(cardNumber)}`);
            return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
        },
    };
}

module.exports = { createPaymentService };
