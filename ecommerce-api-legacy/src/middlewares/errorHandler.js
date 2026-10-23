const { AppError } = require('../utils/errors');

// Express 4 não captura promises rejeitadas: encaminha para o errorHandler
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

function createErrorHandler({ logger }) {
    // eslint-disable-next-line no-unused-vars
    return function errorHandler(err, req, res, next) {
        // Mantém o contrato da baseline: erros respondidos como texto
        if (err instanceof AppError) {
            return res.status(err.statusCode).send(err.message);
        }
        if (err.type === 'entity.parse.failed') {
            return res.status(400).send('Bad Request');
        }
        logger.error(err);
        return res.status(500).send('Erro interno');
    };
}

module.exports = { asyncHandler, createErrorHandler };
