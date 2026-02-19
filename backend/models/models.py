from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Subscriptions(Base):
    """Модель подписки (таблица subscriptions из бота)."""
    __tablename__ = "subscriptions"

    subscription_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    service_id = Column(Integer, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String, nullable=True)  # 'активная' | 'истекла' | 'отключена'
    reminder_sent = Column(Integer, default=0)
    auto_renewal = Column(Boolean, default=True)
    card_details_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Servers(Base):
    __tablename__ = 'servers'

    server_ip = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    limit = Column(Integer, nullable=True)
    hidden = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # Поля для API панели (HTTPS)
    panel_port = Column(Integer, nullable=True)   # порт панели на сервере (14880)
    url_secret = Column(String(255), nullable=True)  # путь панели, напр. /0PkmGmepRhDqrF
    sub_port = Column(Integer, nullable=True)      # порт, на котором отдаётся /sub/ (2096)
    available_ports = Column(String, nullable=True)  # в БД может быть ARRAY; для SQLAlchemy как JSON/текст при необходимости
