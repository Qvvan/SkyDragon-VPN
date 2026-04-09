import time
import uuid

from fastapi.responses import ORJSONResponse
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint, DispatchFunction
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from src.core.logger import AppLogger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Логирует каждый HTTP-запрос: метод, путь, статус, время выполнения и request_id."""
    def __init__(
            self,
            app: ASGIApp,
            logger: AppLogger,
            dispatch: DispatchFunction | None = None
    ):
        super().__init__(app, dispatch)
        self._logger = logger

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())

        start = time.monotonic()
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
        except Exception as e:
            self._logger.exception(
                "Unhandled exception",
                exc=e,
                path=request.url.path,
                method=request.method,
                request_id=request_id,
            )
            return ORJSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "msg": "Internal server error"
                }
            )
        duration_ms = round((time.monotonic() - start) * 1000)
        self._logger.info(
            "Request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        return response
