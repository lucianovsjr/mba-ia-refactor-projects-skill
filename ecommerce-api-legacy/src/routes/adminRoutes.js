const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

function createAdminRoutes(reportController, adminGuard) {
    const router = express.Router();

    router.get('/admin/financial-report', adminGuard, asyncHandler(async (req, res) => {
        res.json(await reportController.financialReport());
    }));

    return router;
}

module.exports = { createAdminRoutes };
