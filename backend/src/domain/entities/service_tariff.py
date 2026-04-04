from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, kw_only=True)
class ServiceTariff:
    service_id: int
    name: str
    duration_days: int
    price: int
