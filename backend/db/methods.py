from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.models import Servers, Subscriptions


async def get_server(session: Session) -> list[Servers]:
    query = (select(Servers).where(Servers.hidden == 0))

    result = await session.execute(query)
    return result.scalars().all()


async def get_subscription_by_user_and_sub_id(
    session: Session, user_id: int, subscription_id: int
) -> Optional[dict]:
    """
    Ищет подписку по user_id и subscription_id, возвращает полную модель (словарь полей).
    """
    query = (
        select(Subscriptions)
        .where(
            Subscriptions.user_id == user_id,
            Subscriptions.subscription_id == subscription_id,
        )
    )
    result = await session.execute(query)
    row = result.scalars().first()
    if row is None:
        return None
    return {
        "subscription_id": row.subscription_id,
        "user_id": row.user_id,
        "service_id": row.service_id,
        "start_date": row.start_date,
        "end_date": row.end_date,
        "status": row.status,
        "reminder_sent": row.reminder_sent,
        "auto_renewal": row.auto_renewal,
        "card_details_id": row.card_details_id,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }
