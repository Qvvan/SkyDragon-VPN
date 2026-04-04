from abc import ABC, abstractmethod

from domain.entities.service_tariff import ServiceTariff


class IServiceTariffRepository(ABC):
    @abstractmethod
    async def list_for_renewal(self) -> list[ServiceTariff]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, service_id: int) -> ServiceTariff | None:
        raise NotImplementedError
