const { PAYMENT_STATUS } = require('../utils/constants');
const { hashPassword, verifyPassword } = require('../utils/crypto');
const { validateCheckoutInput } = require('../utils/validators');
const {
    NotFoundError, PaymentDeclinedError, UnauthorizedError, ValidationError,
} = require('../utils/errors');

function createCheckoutController({ db, userModel, courseModel, enrollmentModel, paymentService, logger }) {
    return {
        async checkout(body) {
            const { name, email, password, courseId, cardNumber } = validateCheckoutInput(body);

            const course = await courseModel.findActiveById(courseId);
            if (!course) throw new NotFoundError('Curso não encontrado');

            const existingUser = await userModel.findByEmail(email);
            if (existingUser && !verifyPassword(password ?? '', existingUser.pass)) {
                throw new UnauthorizedError('Credenciais inválidas');
            }
            if (!existingUser && !password) throw new ValidationError('Bad Request');

            const status = paymentService.charge(cardNumber, course.price);
            if (status !== PAYMENT_STATUS.PAID) throw new PaymentDeclinedError('Pagamento recusado');

            const enrollmentId = await db.transaction(async () => {
                const userId = existingUser
                    ? existingUser.id
                    : await userModel.create({ name, email, passwordHash: hashPassword(password) });
                return enrollmentModel.createWithPayment({
                    userId, courseId: course.id, amount: course.price, status,
                });
            });

            logger.info(`Checkout concluído: curso ${course.id}, matrícula ${enrollmentId}`);
            return { enrollmentId };
        },
    };
}

module.exports = { createCheckoutController };
