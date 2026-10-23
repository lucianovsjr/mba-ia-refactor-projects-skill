const { AsyncLocalStorage } = require('node:async_hooks');
const sqlite3 = require('sqlite3');
const { hashPassword } = require('../utils/crypto');
const { PAYMENT_STATUS, COURSE_ACTIVE } = require('../utils/constants');

function createDatabase(file) {
    const raw = new sqlite3.Database(file);
    const txContext = new AsyncLocalStorage();
    let queue = Promise.resolve();

    const rawRun = (sql, params) => new Promise((resolve, reject) =>
        raw.run(sql, params, function onRun(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        }));
    const rawGet = (sql, params) => new Promise((resolve, reject) =>
        raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row))));
    const rawAll = (sql, params) => new Promise((resolve, reject) =>
        raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows))));

    // Uma única conexão é compartilhada: as operações de fora de uma transação esperam
    // a transação em andamento terminar, para não lerem nem gravarem dentro dela.
    const enqueue = (task) => {
        const result = queue.then(task);
        queue = result.catch(() => {});
        return result;
    };
    const exec = (fn) => (sql, params = []) =>
        (txContext.getStore() ? fn(sql, params) : enqueue(() => fn(sql, params)));

    return {
        run: exec(rawRun),
        get: exec(rawGet),
        all: exec(rawAll),

        transaction(work) {
            if (txContext.getStore()) return work();
            return enqueue(() => txContext.run(true, async () => {
                await rawRun('BEGIN', []);
                try {
                    const value = await work();
                    await rawRun('COMMIT', []);
                    return value;
                } catch (err) {
                    await rawRun('ROLLBACK', []);
                    throw err;
                }
            }));
        },
    };
}

async function initSchema(db) {
    await db.run('PRAGMA foreign_keys = ON');
    await db.run('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, pass TEXT)');
    await db.run('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
    await db.run(`CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER REFERENCES courses(id))`);
    await db.run(`CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL,
        status TEXT)`);
    await db.run('CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');
}

async function seedIfEmpty(db) {
    const { count } = await db.get('SELECT COUNT(*) AS count FROM users');
    if (count > 0) return;

    await db.transaction(async () => {
        await db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            ['Leonan', 'leonan@fullcycle.com.br', hashPassword('123')]);
        await db.run('INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)',
            ['Clean Architecture', 997.00, COURSE_ACTIVE, 'Docker', 497.00, COURSE_ACTIVE]);
        await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
        await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [1, 997.00, PAYMENT_STATUS.PAID]);
    });
}

module.exports = { createDatabase, initSchema, seedIfEmpty };
