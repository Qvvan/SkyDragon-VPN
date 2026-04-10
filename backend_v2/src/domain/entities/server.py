from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class ServerNode:
    server_ip: str
    name: str
    limit: int | None
    hidden: int
    available_ports: str | None
    panel_port: int | None
    url_secret: str | None
    sub_port: int | None
    created_at: datetime | None
