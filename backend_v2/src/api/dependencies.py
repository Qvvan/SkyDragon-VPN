from typing import Annotated

from fastapi import Depends
from fastapi import Request
from fastapi.security import HTTPBearer

from src.core.container import Container
from src.services import ImportService, PaymentService, SubscriptionService

security = HTTPBearer()


def get_container(request: Request) -> Container:
    """
    Получаем Container из app.state.
    Container живет на протяжении всей жизни приложения.
    """
    return request.app.state.container


def get_subscription_service(container: Annotated[Container, Depends(get_container)]) -> SubscriptionService:
    return container.services.subscription_service


def get_import_service(container: Annotated[Container, Depends(get_container)]) -> ImportService:
    return container.services.import_service


def get_payment_service(container: Annotated[Container, Depends(get_container)]) -> PaymentService:
    return container.services.payment_service

