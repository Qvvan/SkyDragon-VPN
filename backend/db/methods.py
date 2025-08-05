from enum import Enum

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from models.models import Keys, Subscriptions
from models.models import Servers


class NameApp(str, Enum):
    OUTLINE = 'Outline'
    VLESS = 'Vless'


async def get_user_keys(session: Session, user_id: int, sub_id: int):
    query = (
        select(Keys.key)
        .join(Subscriptions, Keys.id == func.any(Subscriptions.key_ids))
        .join(Servers, Keys.server_ip == Servers.server_ip)
        .where(
            Subscriptions.user_id == user_id,
            Subscriptions.subscription_id == sub_id,
            Servers.hidden == 0,
            Keys.name_app == NameApp.VLESS
        )
    )

    result = await session.execute(query)
    return result.scalars().all()
