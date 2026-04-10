from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, Response
from starlette import status

from src.api.dependencies import get_subscription_service
from src.api.v1.schemas.subscription import ServicePlanListResponse, ServicePlanSchema, SubscriptionListResponse
from src.services.subscription_service import SubscriptionService

router = APIRouter(tags=["Subscriptions"])


@router.get("/sub/{encrypted_part}")
async def get_subscription(
    encrypted_part: str,
    request: Request,
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    content, headers = await subscription_service.get_subscription_content(
        encrypted_part=encrypted_part,
        user_agent=request.headers.get("user-agent"),
    )
    return Response(content=content, headers=headers)


@router.get("/sub/{encrypted_part}/list", response_model=SubscriptionListResponse)
async def get_subscription_list(
    encrypted_part: str,
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    payload = await subscription_service.get_subscription_list(encrypted_part)
    return SubscriptionListResponse(**payload)


@router.post("/sub/{encrypted_part}/auto-renewal/disable", status_code=status.HTTP_303_SEE_OTHER)
async def disable_auto_renewal(
    encrypted_part: str,
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    await subscription_service.set_auto_renewal(encrypted_part, enabled=False)
    return RedirectResponse(url=f"/api/v1/sub/{encrypted_part}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/sub/{encrypted_part}/auto-renewal/enable", status_code=status.HTTP_303_SEE_OTHER)
async def enable_auto_renewal(
    encrypted_part: str,
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    await subscription_service.set_auto_renewal(encrypted_part, enabled=True)
    return RedirectResponse(url=f"/api/v1/sub/{encrypted_part}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/sub/{encrypted_part}/services", response_model=ServicePlanListResponse)
async def get_services(
    encrypted_part: str,
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    services = await subscription_service.get_services_for_renewal(encrypted_part)
    return ServicePlanListResponse(
        services=[ServicePlanSchema.model_validate(service, from_attributes=True) for service in services]
    )
