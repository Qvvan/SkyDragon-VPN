from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.models import Account, AccountTelegramLink, Subscriptions


class AccountLinkMethods:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_account_by_id(self, account_id: int) -> Account | None:
        result = await self.session.execute(select(Account).filter_by(id=account_id))
        return result.scalars().first()

    async def get_link_by_telegram(self, telegram_user_id: int) -> AccountTelegramLink | None:
        result = await self.session.execute(
            select(AccountTelegramLink).filter_by(telegram_user_id=telegram_user_id)
        )
        return result.scalars().first()

    async def get_link_by_account(self, account_id: int) -> AccountTelegramLink | None:
        result = await self.session.execute(
            select(AccountTelegramLink).filter_by(account_id=account_id)
        )
        return result.scalars().first()

    async def insert_link(self, telegram_user_id: int, account_id: int) -> None:
        self.session.add(AccountTelegramLink(telegram_user_id=telegram_user_id, account_id=account_id))

    async def backfill_subscriptions(self, account_id: int, telegram_user_id: int) -> None:
        await self.session.execute(
            update(Subscriptions)
            .where(Subscriptions.user_id == telegram_user_id, Subscriptions.account_id.is_(None))
            .values(account_id=account_id)
        )
