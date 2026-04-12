from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(slots=True, kw_only=True)
class Payment:
    id: str | None
    payment_id: str
    user_id: int
    recipient_user_id: int | None
    service_id: int | None
    subscription_id: str | None
    # 'subscription' | 'renewal' | 'gift'
    payment_type: str
    # 'pending' | 'succeeded' | 'canceled' | 'failed' | 'refunded'
    status: str
    amount: Decimal
    receipt_link: str | None
    confirmation_url: str | None
    service_name: str | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(slots=True, kw_only=True)
class PaymentCreateResult:
    payment_id: str
    confirmation_url: str
