from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class Server:
    server_ip: str
    name: str
    limit: int | None
    hidden: int | None
    created_at: datetime | None
    panel_port: int | None
    url_secret: str | None
    sub_port: int | None
    available_ports: str | None
