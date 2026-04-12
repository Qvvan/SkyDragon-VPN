from src.api.v1.routes.account import router as account_router
from src.api.v1.routes.auth import router as auth_router
from src.api.v1.routes.imports import router as imports_router
from src.api.v1.routes.payments import router as payments_router
from src.api.v1.routes.services import router as services_router
from src.api.v1.routes.subscriptions import router as subscriptions_router

__all__ = [
    "account_router",
    "auth_router",
    "imports_router",
    "payments_router",
    "services_router",
    "subscriptions_router",
]
