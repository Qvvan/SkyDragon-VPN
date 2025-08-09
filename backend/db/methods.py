from sqlalchemy import select
from sqlalchemy.orm import Session

from models.models import Servers


async def get_server(session: Session) -> list[Servers]:
    query = (select(Servers).where(Servers.hidden == 0))

    result = await session.execute(query)
    return result.scalars().all()
