from fastapi import APIRouter

from api.v1.routes import subscription

api_router = APIRouter()
api_router.include_router(subscription.router)
