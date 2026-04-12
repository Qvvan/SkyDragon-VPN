from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, kw_only=True)
class KeyOperation:
    operation_id: int | None
    user_id: int
    subscription_id: str
    server_id: int
    action: str          # 'create' | 'update' | 'delete' | 'enable' | 'disable'
    days: int | None
    status: str          # 'pending' | 'processing' | 'completed' | 'failed'
    retry_count: int
    max_retries: int
    error_message: str | None
    scheduled_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None
    # Денормализованные поля сервера — заполняются при claim (JOIN с servers)
    server_ip: str | None = None
    server_name: str | None = None
    server_panel_port: int | None = None
    server_url_secret: str | None = None
    server_sub_port: int | None = None
    server_available_ports: str | None = None
