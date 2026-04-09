from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from starlette.requests import Request

from src.core.exceptions import AppError
from src.core.logger import AppLogger


def _error_response(
    status_code: int,
    code: str,
    comment: str,
) -> ORJSONResponse:
    response = ORJSONResponse(
        status_code=status_code,
        content={"status": "error", "code": code, "comment": comment, "obj": None},
    )
    return response


def _get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def register_errors(app: FastAPI, app_logger: AppLogger) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(req: Request, exc: AppError) -> ORJSONResponse:
        request_id = _get_request_id(req)
        app_logger.warning(
            "App error",
            path=req.url.path,
            method=req.method,
            request_id=request_id,
            code=exc.code,
            comment=exc.message,
            status=exc.http_status_code,
        )
        return _error_response(exc.http_status_code, exc.code, exc.message)