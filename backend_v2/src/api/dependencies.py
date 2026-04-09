from fastapi import Request
from fastapi.security import HTTPBearer

from src.core.container import Container

security = HTTPBearer()


def get_container(request: Request) -> Container:
    """
    Получаем Container из app.state.
    Container живет на протяжении всей жизни приложения.
    """
    return request.app.state.container

