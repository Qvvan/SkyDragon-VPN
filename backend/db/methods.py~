from sqlalchemy import select, func
from sqlalchemy.orm import Session

from models.models import Keys, Subscriptions


async def get_user_keys(session: Session, user_id: int):
    query = (
        select(Keys.key)
        .join(Subscriptions, Keys.id == func.any(Subscriptions.key_ids))  # Проверяем, есть ли ключ в массиве
        .where(Subscriptions.user_id == user_id)
    )

    result = await session.execute(query)
    return result.scalars().all()
