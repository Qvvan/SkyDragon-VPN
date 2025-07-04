from sqlalchemy import select, func
from sqlalchemy.orm import Session

from models.models import Servers
from models.models import Keys, Subscriptions


async def get_user_keys(session: Session, user_id: int, sub_id: int):
    query = (
        select(Keys.key)
        .join(Subscriptions, Keys.id == func.any(Subscriptions.key_ids))
        .join(Servers, Keys.server_ip == Servers.server_ip)  # Добавляем join с серверами
        .where(
            Subscriptions.user_id == user_id,
            Subscriptions.subscription_id == sub_id,
            Servers.hidden == 0
        )
    )

    result = await session.execute(query)
    return result.scalars().all()
