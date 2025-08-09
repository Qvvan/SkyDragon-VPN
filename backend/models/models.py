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
