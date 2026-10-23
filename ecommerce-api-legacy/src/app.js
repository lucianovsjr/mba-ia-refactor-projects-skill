const config = require('./config');
const logger = require('./utils/logger');
const { buildApp } = require('./server');

buildApp({ config, logger })
    .then(({ app }) => {
        app.listen(config.port, () => logger.info(`LMS API rodando na porta ${config.port}`));
    })
    .catch((err) => {
        logger.error('Falha ao iniciar a aplicação', err);
        process.exit(1);
    });
