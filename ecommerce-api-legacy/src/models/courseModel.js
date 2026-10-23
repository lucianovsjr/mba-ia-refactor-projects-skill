const { COURSE_ACTIVE } = require('../utils/constants');

function createCourseModel(db) {
    return {
        findActiveById: (courseId) =>
            db.get('SELECT id, title, price FROM courses WHERE id = ? AND active = ?', [courseId, COURSE_ACTIVE]),
    };
}

module.exports = { createCourseModel };
