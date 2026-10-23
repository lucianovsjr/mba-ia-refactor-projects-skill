const express = require('express');
const defaultConfig = require('./config');
const defaultLogger = require('./utils/logger');
const { createDatabase, initSchema, seedIfEmpty } = require('./database/connection');
const { createUserModel } = require('./models/userModel');
const { createCourseModel } = require('./models/courseModel');
const { createEnrollmentModel } = require('./models/enrollmentModel');
const { createReportModel } = require('./models/reportModel');
const { createPaymentService } = require('./services/paymentService');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createCheckoutRoutes } = require('./routes/checkoutRoutes');
const { createAdminRoutes } = require('./routes/adminRoutes');
const { createUserRoutes } = require('./routes/userRoutes');
const { createAdminGuard } = require('./middlewares/adminGuard');
const { createErrorHandler } = require('./middlewares/errorHandler');

// Composition root: monta banco, models, services e controllers e injeta nas rotas
async function buildApp({ config = defaultConfig, logger = defaultLogger, db } = {}) {
    const database = db || createDatabase(config.databaseFile);
    await initSchema(database);
    await seedIfEmpty(database);

    const userModel = createUserModel(database);
    const courseModel = createCourseModel(database);
    const enrollmentModel = createEnrollmentModel(database);
    const reportModel = createReportModel(database);
    const paymentService = createPaymentService({ logger });

    const checkoutController = createCheckoutController({
        db: database, userModel, courseModel, enrollmentModel, paymentService, logger,
    });
    const reportController = createReportController({ reportModel });
    const userController = createUserController({ db: database, userModel });
    const adminGuard = createAdminGuard({ adminToken: config.adminToken });

    const app = express();
    app.use(express.json());
    app.use('/api', createCheckoutRoutes(checkoutController));
    app.use('/api', createAdminRoutes(reportController, adminGuard));
    app.use('/api', createUserRoutes(userController, adminGuard));
    app.use(createErrorHandler({ logger }));

    return { app, db: database };
}

module.exports = { buildApp };
