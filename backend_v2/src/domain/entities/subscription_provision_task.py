from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class SubscriptionProvisionTask:
    id: int | None
    subscription_id: int
    user_id: int
    server_ip: str
    action: str          # 'create' | 'update' | 'delete'
    status: str          # 'pending' | 'processing' | 'done' | 'failed'
    attempts: int
    max_attempts: int
    last_error: str | None
    expire_at: datetime | None
    scheduled_at: datetime
    done_at: datetime | None
    created_at: datetime | None
    # Денормализованные поля сервера — заполняются при claim (JOIN с servers)
    server_name: str | None = None
    server_panel_port: int | None = None
    server_url_secret: str | None = None
    server_sub_port: int | None = None
