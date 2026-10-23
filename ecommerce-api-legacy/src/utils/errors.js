class AppError extends Error {
    constructor(message, statusCode = 400) {
        super(message);
        this.statusCode = statusCode;
    }
}

class ValidationError extends AppError {
    constructor(message) { super(message, 400); }
}

class PaymentDeclinedError extends AppError {
    constructor(message) { super(message, 400); }
}

class UnauthorizedError extends AppError {
    constructor(message) { super(message, 401); }
}

class ForbiddenError extends AppError {
    constructor(message) { super(message, 403); }
}

class NotFoundError extends AppError {
    constructor(message) { super(message, 404); }
}

module.exports = {
    AppError,
    ValidationError,
    PaymentDeclinedError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
};
