from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.dependencies import get_service_plan_service
from src.api.v1.schemas.subscription import ServicePlanListResponse, ServicePlanSchema
from src.services.service_plan_service import ServicePlanService

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("", response_model=ServicePlanListResponse)
async def list_services(
    service_plan_service: Annotated[ServicePlanService, Depends(get_service_plan_service)],
):
    services = await service_plan_service.list_all()
    return ServicePlanListResponse(
        services=[ServicePlanSchema.model_validate(s, from_attributes=True) for s in services],
    )
