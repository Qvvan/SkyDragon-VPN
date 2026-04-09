from fastapi import APIRouter

from src.api.health import router as health_router
from src.api.v1 import v1_router

router = APIRouter()
router.include_router(v1_router)
router.include_router(health_router)

__all__ = ["router"]
