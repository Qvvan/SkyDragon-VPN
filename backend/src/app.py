from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from starlette.templating import Jinja2Templates

from backend.src.api.v1.router import api_router
from backend.src.core import Config
from backend.src.core.container import Container
from backend.src.core.exceptions import AppError


@asynccontextmanager
async def lifespan(app: FastAPI):
    backend_dir = Path(__file__).resolve().parent
    config = Config.load(
        env_file=backend_dir / ".env",
        yaml_file=backend_dir / "config.yaml",
    )
    container = Container(config)
    await container.infra.postgres_db.connect()
    app.state.container = container
    app.state.templates = Jinja2Templates(directory=str(backend_dir / "templates"))
    app.title = config.app.NAME
    yield
    await container.closer()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def _app_error_handler(_request: Request, exc: AppError) -> PlainTextResponse:
        return PlainTextResponse(exc.message, status_code=exc.http_status_code)

    app.include_router(api_router)
    return app


app = create_app()
