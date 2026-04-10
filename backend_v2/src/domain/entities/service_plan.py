from dataclasses import dataclass


@dataclass(slots=True, kw_only=True)
class ServicePlan:
    service_id: int
    name: str
    duration_days: int
    price: int

    @property
    def is_trial(self) -> bool:
        return self.service_id == 0
