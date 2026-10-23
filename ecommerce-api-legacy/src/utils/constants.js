const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// Regra do gateway simulado: cartões que começam com este prefixo são aprovados
const APPROVED_CARD_PREFIX = '4';

const COURSE_ACTIVE = 1;

const UNKNOWN_STUDENT = 'Unknown';

module.exports = { PAYMENT_STATUS, APPROVED_CARD_PREFIX, COURSE_ACTIVE, UNKNOWN_STUDENT };
