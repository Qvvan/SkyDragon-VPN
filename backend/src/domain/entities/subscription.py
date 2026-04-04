from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class Subscription:
    subscription_id: int
    user_id: int
    service_id: int | None
    start_date: datetime | None
    end_date: datetime | None
    status: str | None
    reminder_sent: int | None
    auto_renewal: bool | None
    card_details_id: str | None
    created_at: datetime | None
    updated_at: datetime | None
    service_name: str | None = None
    service_duration_days: int | None = None
    service_price: int | None = None

    def is_active(self, *, active_status_label: str, now: datetime) -> bool:
        if self.status != active_status_label:
            return False
        if self.end_date is None:
            return True
        end = self.end_date
        if end.tzinfo is not None:
            end = end.replace(tzinfo=None)
        now_naive = now.replace(tzinfo=None) if now.tzinfo else now
        return end >= now_naive

    def expire_unix(self) -> int:
        if not self.end_date:
            return 0
        end = self.end_date
        if hasattr(end, "timestamp"):
            return int(end.timestamp())
        return 0
