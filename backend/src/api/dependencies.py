from typing import Annotated

from fastapi import Depends, Request

from core.container import Container
from services.public_subscription_service import PublicSubscriptionService


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_public_subscription_service(
    container: Annotated[Container, Depends(get_container)],
) -> PublicSubscriptionService:
    return container.services.public_subscription_service
