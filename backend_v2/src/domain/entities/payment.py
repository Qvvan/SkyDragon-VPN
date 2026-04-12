from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class Payment:
    id: str | None
    payment_id: str
    user_id: int
    recipient_user_id: int | None
    service_id: int | None
    status: str
    payment_type: str | None
    receipt_link: str | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(slots=True, kw_only=True)
class PaymentCreateResult:
    payment_id: str
    confirmation_url: str
