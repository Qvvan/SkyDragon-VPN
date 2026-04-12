from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class ServicePlan:
    service_id: int
    name: str
    description: str | None
    duration_days: int
    price: int
    original_price: int | None
    is_trial: bool
    is_active: bool
    is_featured: bool
    sort_order: int
    badge: str | None
    created_at: datetime
    updated_at: datetime
