from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.container import Container
from src.core.exceptions import AuthenticationError
from src.domain.entities.account import Account
from src.interfaces.services.bot_api_secret_verifier import IBotApiSecretVerifier
from src.services import ImportService, PaymentService, ServicePlanService, SubscriptionService
from src.services.auth_service import AuthService
from src.services.telegram_account_link_service import TelegramAccountLinkService

bearer_scheme = HTTPBearer(auto_error=False)


def get_container(request: Request) -> Container:
    """
    Получаем Container из app.state.
    Container живет на протяжении всей жизни приложения.
    """
    return request.app.state.container


def get_subscription_service(container: Annotated[Container, Depends(get_container)]) -> SubscriptionService:
    return container.services.subscription_service


def get_service_plan_service(container: Annotated[Container, Depends(get_container)]) -> ServicePlanService:
    return container.services.service_plan_service


def get_import_service(container: Annotated[Container, Depends(get_container)]) -> ImportService:
    return container.services.import_service


def get_payment_service(container: Annotated[Container, Depends(get_container)]) -> PaymentService:
    return container.services.payment_service


def get_auth_service(container: Annotated[Container, Depends(get_container)]) -> AuthService:
    return container.services.auth_service


def get_telegram_account_link_service(
    container: Annotated[Container, Depends(get_container)],
) -> TelegramAccountLinkService:
    return container.services.telegram_account_link_service


def get_bot_api_secret_verifier(
    container: Annotated[Container, Depends(get_container)],
) -> IBotApiSecretVerifier:
    return container.services.bot_api_secret_verifier


async def get_current_account(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Account:
    if creds is None or creds.scheme.lower() != "bearer":
        raise AuthenticationError("Требуется авторизация")
    return await auth_service.require_account(creds.credentials)


def require_bot_api_secret(
    verifier: Annotated[IBotApiSecretVerifier, Depends(get_bot_api_secret_verifier)],
    x_bot_secret: Annotated[str | None, Header(alias="X-Bot-Secret")] = None,
) -> None:
    verifier.assert_valid(x_bot_secret)
