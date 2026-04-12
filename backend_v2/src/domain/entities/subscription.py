from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class SubscriptionStatus(str, Enum):
    ACTIVE = "активная"
    EXPIRED = "истекла"
    DISABLED = "отключена"


@dataclass(slots=True, kw_only=True)
class Subscription:
    subscription_id: str
    user_id: int
    account_id: str | None = None
    service_id: int | None
    start_date: datetime | None
    end_date: datetime | None
    status: str | None
    reminder_sent: int
    auto_renewal: bool
    card_details_id: str | None
    created_at: datetime | None
    updated_at: datetime | None
    service_name: str | None = None
    service_duration_days: int | None = None
    service_price: int | None = None
    import_url: str | None = None

    def is_active(self) -> bool:
        if self.status != SubscriptionStatus.ACTIVE.value:
            return False
        if self.end_date is None:
            return True
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return self.end_date.replace(tzinfo=None) >= now

    def expire_unix(self) -> int:
        if self.end_date is None:
            return 0
        return int(self.end_date.timestamp())
