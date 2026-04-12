from abc import ABC, abstractmethod

from src.domain.entities.service_plan import ServicePlan


class IServicePlanRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[ServicePlan]:
        """Все активные платные планы (is_trial=FALSE, is_active=TRUE), по sort_order."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, service_id: int) -> ServicePlan | None:
        raise NotImplementedError

    @abstractmethod
    async def get_trial(self) -> ServicePlan | None:
        """Возвращает триальный план (is_trial=TRUE, is_active=TRUE)."""
        raise NotImplementedError
