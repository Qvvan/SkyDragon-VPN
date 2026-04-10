from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class Account:
    """Учётная запись сайта (не путать с telegram user_id в legacy-колонке subscriptions.user_id)."""

    id: int
    email: str | None
    phone: str | None
    first_name: str
    last_name: str
    password_hash: str
    created_at: datetime
    updated_at: datetime
