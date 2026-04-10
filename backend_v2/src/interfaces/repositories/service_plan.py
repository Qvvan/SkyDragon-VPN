from abc import ABC, abstractmethod

from src.domain.entities.service_plan import ServicePlan


class IServicePlanRepository(ABC):
    @abstractmethod
    async def list_for_renewal(self) -> list[ServicePlan]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, service_id: int) -> ServicePlan | None:
        raise NotImplementedError
