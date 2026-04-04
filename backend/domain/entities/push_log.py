from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class PushLog:
    id: int
    message: str
    user_ids: list[int]
    timestamp: datetime | None
