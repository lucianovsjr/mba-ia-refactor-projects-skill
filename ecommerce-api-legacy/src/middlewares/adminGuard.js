const crypto = require('node:crypto');
const { ForbiddenError } = require('../utils/errors');

const safeEqual = (a, b) => {
    const bufA = Buffer.from(a);
    const bufB = Buffer.from(b);
    return bufA.length === bufB.length && crypto.timingSafeEqual(bufA, bufB);
};

// Opt-in: sem ADMIN_TOKEN configurado as rotas continuam públicas (contrato original)
function createAdminGuard({ adminToken }) {
    return function adminGuard(req, res, next) {
        if (!adminToken) return next();
        if (!safeEqual(req.get('X-Admin-Token') || '', adminToken)) {
            return next(new ForbiddenError('Acesso negado'));
        }
        return next();
    };
}

module.exports = { createAdminGuard };
