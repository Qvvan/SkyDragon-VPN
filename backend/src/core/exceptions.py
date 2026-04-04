from starlette import status


class AppError(Exception):
    """Базовое исключение приложения"""
    http_status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR

    __slots__ = (
        "code",
        "message"
    )

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationError(AppError):
    """Исключения валидации (в т.ч. неверная подпись ссылки подписки)."""
    http_status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class NotFoundError(AppError):
    """Сущность не найдена"""
    http_status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, message: str):
        super().__init__(message, "NOT_FOUND")


class ConflictError(AppError):
    """Конфликт данных"""
    http_status_code = status.HTTP_409_CONFLICT

    def __init__(self, message: str):
        super().__init__(message, "CONFLICT")


class AuthenticationError(AppError):
    """Ошибка аутентификации"""
    http_status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, message: str):
        super().__init__(message, "AUTHENTICATION_ERROR")


class UnauthorizedError(AppError):
    """Неавторизованный доступ"""
    http_status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, message: str):
        super().__init__(message, "UNAUTHORIZED")


class ForbiddenError(AppError):
    """Доступ запрещен"""
    http_status_code = status.HTTP_403_FORBIDDEN

    def __init__(self, message: str):
        super().__init__(message, "FORBIDDEN")


class ServiceUnavailableError(AppError):
    http_status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    def __init__(self, message: str):
        super().__init__(message, "SERVICE_UNAVAILABLE")

