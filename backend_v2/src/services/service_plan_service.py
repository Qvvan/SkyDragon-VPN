from src.domain.entities.service_plan import ServicePlan
from src.interfaces.repositories.service_plan import IServicePlanRepository


class ServicePlanService:
    __slots__ = ("_service_plan_repo",)

    def __init__(self, service_plan_repo: IServicePlanRepository) -> None:
        self._service_plan_repo = service_plan_repo

    async def list_all(self) -> list[ServicePlan]:
        return await self._service_plan_repo.list_for_renewal()
