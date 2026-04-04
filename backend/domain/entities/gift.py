from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class Gift:
    gift_id: int
    giver_id: int
    recipient_user_id: int
    service_id: int | None
    status: str
    activated_at: datetime | None
    created_at: datetime | None
