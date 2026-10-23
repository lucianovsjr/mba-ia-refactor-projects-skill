function createEnrollmentModel(db) {
    return {
        // Deve ser chamado dentro de db.transaction(): matrícula, pagamento e auditoria são atômicos
        async createWithPayment({ userId, courseId, amount, status }) {
            const { lastID: enrollmentId } = await db.run(
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
            await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
                [enrollmentId, amount, status]);
            await db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
                [`Checkout curso ${courseId} por ${userId}`]);
            return enrollmentId;
        },
    };
}

module.exports = { createEnrollmentModel };
