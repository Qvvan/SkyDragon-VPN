from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models.models import Servers, Subscriptions, Services, Payments


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
        select(
            Subscriptions,
            Services.name.label("service_name"),
            Services.duration_days.label("service_duration_days"),
            Services.price.label("service_price"),
        )
        .outerjoin(Services, Subscriptions.service_id == Services.service_id)
        .where(
            Subscriptions.user_id == user_id,
            Subscriptions.subscription_id == subscription_id,
        )
    )
    result = await session.execute(query)
    row = result.first()
    if row is None or row[0] is None:
        return None
    sub = row[0]
    return {
        "subscription_id": sub.subscription_id,
        "user_id": sub.user_id,
        "service_id": sub.service_id,
        "start_date": sub.start_date,
        "end_date": sub.end_date,
        "status": sub.status,
        "reminder_sent": sub.reminder_sent,
        "auto_renewal": sub.auto_renewal,
        "card_details_id": sub.card_details_id,
        "created_at": sub.created_at,
        "updated_at": sub.updated_at,
        "service_name": row.service_name,
        "service_duration_days": row.service_duration_days,
        "service_price": row.service_price,
    }


async def disable_auto_renewal_by_user_and_sub_id(
    session: Session,
    user_id: int,
    subscription_id: int,
) -> bool:
    query = (
        update(Subscriptions)
        .where(
            Subscriptions.user_id == user_id,
            Subscriptions.subscription_id == subscription_id,
        )
        .values(auto_renewal=False)
    )
    result = await session.execute(query)
    await session.commit()
    return bool(result.rowcount)


async def enable_auto_renewal_by_user_and_sub_id(
    session: Session,
    user_id: int,
    subscription_id: int,
) -> bool:
    query = (
        update(Subscriptions)
        .where(
            Subscriptions.user_id == user_id,
            Subscriptions.subscription_id == subscription_id,
        )
        .values(auto_renewal=True)
    )
    result = await session.execute(query)
    await session.commit()
    return bool(result.rowcount)


async def get_services_for_renewal(session: Session) -> list[dict]:
    result = await session.execute(
        select(Services)
        .where(Services.service_id > 0)
        .order_by(Services.duration_days.asc())
    )
    services = result.scalars().all()
    return [
        {
            "service_id": s.service_id,
            "name": s.name,
            "duration_days": s.duration_days,
            "price": s.price,
        }
        for s in services
    ]


async def get_service_by_id(session: Session, service_id: int) -> Optional[dict]:
    result = await session.execute(select(Services).where(Services.service_id == service_id))
    service = result.scalars().first()
    if not service:
        return None
    return {
        "service_id": service.service_id,
        "name": service.name,
        "duration_days": service.duration_days,
        "price": service.price,
    }


async def create_pending_payment(
    session: Session,
    *,
    payment_id: str,
    user_id: int,
    service_id: int,
) -> None:
    session.add(
        Payments(
            payment_id=payment_id,
            user_id=user_id,
            service_id=service_id,
            status="pending",
        )
    )
    await session.commit()
