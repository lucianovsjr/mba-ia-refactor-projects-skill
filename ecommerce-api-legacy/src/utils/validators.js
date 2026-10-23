const { ValidationError } = require('./errors');

// A baseline respondia "Bad Request" para qualquer entrada inválida no checkout
const BAD_REQUEST = 'Bad Request';
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CARD_REGEX = /^\d{12,19}$/;

const isNonEmptyString = (value) => typeof value === 'string' && value.trim().length > 0;

function parsePositiveInt(value) {
    if (typeof value === 'number' && Number.isInteger(value) && value > 0) return value;
    if (typeof value === 'string' && /^\d+$/.test(value) && Number(value) > 0) return Number(value);
    return null;
}

function validateCheckoutInput(body) {
    const { usr, eml, pwd, c_id: rawCourseId, card } = body || {};
    if (!isNonEmptyString(usr) || !isNonEmptyString(eml) || !EMAIL_REGEX.test(eml)) {
        throw new ValidationError(BAD_REQUEST);
    }
    const courseId = parsePositiveInt(rawCourseId);
    if (courseId === null) throw new ValidationError(BAD_REQUEST);
    if (typeof card !== 'string') throw new ValidationError(BAD_REQUEST);
    const cardNumber = card.replace(/[\s-]/g, '');
    if (!CARD_REGEX.test(cardNumber)) throw new ValidationError(BAD_REQUEST);
    if (pwd !== undefined && typeof pwd !== 'string') throw new ValidationError(BAD_REQUEST);

    return { name: usr.trim(), email: eml.trim(), password: pwd, courseId, cardNumber };
}

function parseUserId(value) {
    const userId = parsePositiveInt(value);
    if (userId === null) throw new ValidationError(BAD_REQUEST);
    return userId;
}

module.exports = { validateCheckoutInput, parseUserId };
