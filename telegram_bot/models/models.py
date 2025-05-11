from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Enum, BigInteger, ARRAY, Boolean, Text, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SubscriptionStatusEnum(str, Enum):
    ACTIVE = 'активная'
    EXPIRED = 'истекла'
    OFF = 'отключена'


class NameApp(str, Enum):
    OUTLINE = 'Outline'
    VLESS = 'Vless'


class StatusSubscriptionHistory(str, Enum):
    NEW_SUBSCRIPTION = 'новая подписка'
    EXTENSION = 'продление'


class ReferralStatus(str, Enum):
    """Status of a referral in the db"""
    INVITED = 'приглашен'
    SUBSCRIBED = 'купил'


class Users(Base):
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True, nullable=False)
    username = Column(String)
    ban = Column(Boolean, default=False)
    trial_used = Column(Boolean, default=False)
    reminder_trial_sub = Column(Boolean, default=False)
    last_visit = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Referrals(Base):
    __tablename__ = 'referrals'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    referred_id = Column(BigInteger, nullable=False)  # ID приглашённого пользователя
    referrer_id = Column(BigInteger, nullable=False)  # ID пригласившего пользователя
    bonus_issued = Column(String, default=ReferralStatus.INVITED)  # Статус бонуса
    invited_username = Column(String, nullable=True)  # Имя приглашенного
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Services(Base):
    __tablename__ = 'services'

    service_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    duration_days = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)


class Keys(Base):
    __tablename__ = 'keys'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_id = Column(Integer, nullable=False)
    key = Column(String, nullable=False)
    server_ip = Column(String, nullable=False)
    email = Column(String, nullable=True)
    name_app = Column(String, nullable=False)
    status = Column(String, default='active', nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Subscriptions(Base):
    __tablename__ = 'subscriptions'

    subscription_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False) #ID пользователя
    service_id = Column(Integer, nullable=True) #ID сервиса
    config_link = Column(String, nullable=True) #Ссылка на конфиг
    key_ids = Column(ARRAY(Integer), default=[], nullable=True) #ID ключей
    start_date = Column(DateTime, nullable=True) #Дата начала
    end_date = Column(DateTime, nullable=True) #Дата окончания
    status = Column(String, default=SubscriptionStatusEnum.ACTIVE) #Статус активная подписка или истекла
    reminder_sent = Column(Integer, default=0) #Было ли отправлено напоминание
    auto_renewal = Column(Boolean, default=True) #Включено ли автопродление по данной подписке
    card_details_id = Column(String, nullable=True) #Данные карты, для автопродления
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FamilyMembers(Base):
    __tablename__ = "family_members"

    family_id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_id = Column(Integer, nullable=False)
    user_id = Column(BigInteger, nullable=True)
    role = Column(String, default="member")  # owner / member
    is_free = Column(Boolean, default=True)  # True, если место свободно
    joined_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SubscriptionsHistory(Base):
    __tablename__ = 'subscriptions_history'

    subscription_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True)
    service_id = Column(Integer, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Payments(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(String, nullable=False, unique=True)
    user_id = Column(BigInteger, nullable=False)
    service_id = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default='pending')
    receipt_link = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Gifts(Base):
    __tablename__ = 'gifts'

    gift_id = Column(Integer, primary_key=True, autoincrement=True)
    giver_id = Column(BigInteger, nullable=False)
    receiver_username = Column(String, nullable=False)
    service_id = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default='pending')
    activated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Servers(Base):
    __tablename__ = 'servers'

    server_ip = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    limit = Column(Integer, nullable=True)
    hidden = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Pushes(Base):
    __tablename__ = 'pushes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(String, nullable=False)
    user_ids = Column(ARRAY(BigInteger), default=[])
    timestamp = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    subscription_id = Column(BigInteger, nullable=True)  # ID подписки, если уведомление связано с подпиской
    notification_type = Column(String, nullable=False)  # Тип уведомления (no_connection, payment_reminder, etc.)
    message = Column(Text, nullable=True)  # Текст уведомления
    status = Column(String, default="active")  # Статус: active, resolved, expired
    additional_data = Column(JSON, nullable=True)  # Дополнительные данные
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)