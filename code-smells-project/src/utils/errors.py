class AppError(Exception):
    """Erro de domínio. O error handler central traduz para status + JSON.

    `com_sucesso` acrescenta `"sucesso": false` ao corpo, preservando o formato
    que cada endpoint já devolvia antes da refatoração.
    """

    status_code = 400

    def __init__(self, message, com_sucesso=False):
        super().__init__(message)
        self.message = message
        self.com_sucesso = com_sucesso


class ValidationError(AppError):
    status_code = 400


class BusinessRuleError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409
