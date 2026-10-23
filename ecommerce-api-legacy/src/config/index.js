const config = Object.freeze({
    port: Number(process.env.PORT) || 3000,
    databaseFile: process.env.DATABASE_FILE || ':memory:',
    logLevel: process.env.LOG_LEVEL || 'info',
    // Opcional: quando definido, as rotas administrativas exigem o header X-Admin-Token
    adminToken: process.env.ADMIN_TOKEN || '',
});

module.exports = config;
