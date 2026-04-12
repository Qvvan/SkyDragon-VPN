from fastapi import APIRouter

from src.api.v1.routes import (
    account_router,
    auth_router,
    imports_router,
    payments_router,
    services_router,
    subscriptions_router,
)

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(subscriptions_router)
v1_router.include_router(imports_router)
v1_router.include_router(payments_router)
v1_router.include_router(auth_router)
v1_router.include_router(account_router)
v1_router.include_router(services_router)

__all__ = ["v1_router"]
