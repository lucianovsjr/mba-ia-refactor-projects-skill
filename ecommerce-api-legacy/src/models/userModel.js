function createUserModel(db) {
    return {
        findByEmail: (email) =>
            db.get('SELECT id, name, email, pass FROM users WHERE email = ?', [email]),

        async create({ name, email, passwordHash }) {
            const { lastID } = await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
                [name, email, passwordHash]);
            return lastID;
        },

        // Matrículas e pagamentos saem junto via ON DELETE CASCADE
        async deleteById(userId) {
            const { changes } = await db.run('DELETE FROM users WHERE id = ?', [userId]);
            return changes > 0;
        },
    };
}

module.exports = { createUserModel };
