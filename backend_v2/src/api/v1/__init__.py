from fastapi import APIRouter

from src.api.v1.routes import imports_router, payments_router, subscriptions_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(subscriptions_router)
v1_router.include_router(imports_router)
v1_router.include_router(payments_router)

__all__ = ["v1_router"]
