from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from models.models import *


async def get_user_keys(session: Session, user_id: int):
        query = (
            select(Keys.key)
            .join(Subscriptions, Keys.id.in_(Subscriptions.key_ids))
            .where(Subscriptions.user_id == user_id)
        )

        return session.execute(query).scalars().all()

