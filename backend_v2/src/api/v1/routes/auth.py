from typing import Annotated

from fastapi import APIRouter, Depends, Request

from src.api.dependencies import get_auth_service
from src.api.rate_limit import limiter
from src.api.v1.schemas.account import LoginRequest, RegisterRequest, TokenResponse
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse)
@limiter.limit("10/minute")
async def register(
    request: Request,
    data: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    _, token = await auth_service.register(
        login=data.login,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
    )
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/minute")
async def login(
    request: Request,
    data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    _, token = await auth_service.login(login=data.login, password=data.password)
    return TokenResponse(access_token=token)
