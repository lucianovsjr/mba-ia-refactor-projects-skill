const config = require('../config');

const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const threshold = LEVELS[config.logLevel] ?? LEVELS.info;

const log = (level) => (...args) => {
    if (LEVELS[level] <= threshold) {
        console[level === 'debug' ? 'log' : level](`[${level.toUpperCase()}]`, ...args);
    }
};

module.exports = { error: log('error'), warn: log('warn'), info: log('info'), debug: log('debug') };
