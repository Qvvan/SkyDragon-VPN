from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class Payment:
    id: int
    payment_id: str
    user_id: int
    recipient_user_id: int | None
    service_id: int | None
    status: str
    payment_type: str | None
    receipt_link: str | None
    created_at: datetime | None
    updated_at: datetime | None
