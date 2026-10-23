const { parseUserId } = require('../utils/validators');
const { NotFoundError } = require('../utils/errors');

function createUserController({ db, userModel }) {
    return {
        async deleteUser(rawUserId) {
            const userId = parseUserId(rawUserId);
            const deleted = await db.transaction(() => userModel.deleteById(userId));
            if (!deleted) throw new NotFoundError('Usuário não encontrado');
        },
    };
}

module.exports = { createUserController };
