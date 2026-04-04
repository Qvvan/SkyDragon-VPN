from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True, kw_only=True)
class UserNotification:
    id: int
    user_id: int
    subscription_id: int | None
    notification_type: str
    message: str | None
    status: str | None
    additional_data: dict[str, Any] | list[Any] | None
    created_at: datetime | None
    updated_at: datetime | None
