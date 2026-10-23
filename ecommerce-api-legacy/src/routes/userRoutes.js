const express = require('express');
const { asyncHandler } = require('../middlewares/errorHandler');

function createUserRoutes(userController, adminGuard) {
    const router = express.Router();

    router.delete('/users/:id', adminGuard, asyncHandler(async (req, res) => {
        await userController.deleteUser(req.params.id);
        res.send('Usuário deletado');
    }));

    return router;
}

module.exports = { createUserRoutes };
