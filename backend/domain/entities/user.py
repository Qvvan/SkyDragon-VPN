from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class User:
    user_id: int
    username: str | None
    ban: bool | None
    trial_used: bool | None
    reminder_trial_sub: bool | None
    last_visit: datetime | None
    created_at: datetime | None
