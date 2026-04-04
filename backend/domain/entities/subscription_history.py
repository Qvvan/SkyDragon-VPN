from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class SubscriptionHistory:
    subscription_id: int
    user_id: int | None
    service_id: int | None
    start_date: datetime | None
    end_date: datetime | None
    status: str | None
    created_at: datetime | None
    updated_at: datetime | None
