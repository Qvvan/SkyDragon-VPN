from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


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
