from datetime import datetime

from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Keys(Base):
    __tablename__ = 'keys'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_id = Column(Integer, nullable=False)
    key = Column(String, nullable=False)
    server_ip = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Subscriptions(Base):
    __tablename__ = 'subscriptions'

    subscription_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    key_ids = Column(ARRAY(Integer), default=[], nullable=True)
