const crypto = require('node:crypto');

const SALT_BYTES = 16;
const KEY_LENGTH = 64;
const SCHEME = 'scrypt';

function hashPassword(password) {
    const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
    const derived = crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex');
    return `${SCHEME}$${salt}$${derived}`;
}

function verifyPassword(password, stored) {
    const [scheme, salt, expected] = String(stored).split('$');
    if (scheme !== SCHEME || !salt || !expected) return false;
    const derived = crypto.scryptSync(password, salt, KEY_LENGTH);
    const expectedBuf = Buffer.from(expected, 'hex');
    return expectedBuf.length === derived.length && crypto.timingSafeEqual(derived, expectedBuf);
}

module.exports = { hashPassword, verifyPassword };
