from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class Referral:
    id: int
    referred_id: int
    referrer_id: int
    bonus_issued: str | None
    invited_username: str | None
    created_at: datetime | None
