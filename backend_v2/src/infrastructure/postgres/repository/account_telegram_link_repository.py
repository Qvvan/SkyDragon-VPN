from datetime import datetime

from src.interfaces.clients.db.query_executor import IQueryExecutor
from src.interfaces.repositories.account_telegram_link import IAccountTelegramLinkRepository


class PostgresAccountTelegramLinkRepository(IAccountTelegramLinkRepository):
    __slots__ = ("_query_executor",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._query_executor = query_executor

    async def get_account_id_by_telegram(self, telegram_user_id: int) -> int | None:
        query = """
            SELECT account_id
            FROM account_telegram_links
            WHERE telegram_user_id = $1
        """
        row = await self._query_executor.fetch_row(query, telegram_user_id)
        return int(row["account_id"]) if row else None

    async def get_telegram_id_by_account(self, account_id: int) -> int | None:
        query = """
            SELECT telegram_user_id
            FROM account_telegram_links
            WHERE account_id = $1
        """
        row = await self._query_executor.fetch_row(query, account_id)
        return int(row["telegram_user_id"]) if row else None

    async def replace_link_code(self, account_id: int, code: str, expires_at: datetime) -> None:
        await self._query_executor.execute("DELETE FROM telegram_link_codes WHERE account_id = $1", account_id)
        await self._query_executor.execute(
            """
            INSERT INTO telegram_link_codes (code, account_id, expires_at)
            VALUES ($1, $2, $3)
            """,
            code,
            account_id,
            expires_at,
        )

    async def peek_valid_link_code(self, code: str) -> int | None:
        query = """
            SELECT account_id
            FROM telegram_link_codes
            WHERE code = $1 AND expires_at > CURRENT_TIMESTAMP
        """
        row = await self._query_executor.fetch_row(query, code)
        return int(row["account_id"]) if row else None

    async def take_valid_link_code(self, code: str) -> int | None:
        query = """
            DELETE FROM telegram_link_codes
            WHERE code = $1 AND expires_at > CURRENT_TIMESTAMP
            RETURNING account_id
        """
        row = await self._query_executor.fetch_row(query, code)
        return int(row["account_id"]) if row else None

    async def insert_link(self, telegram_user_id: int, account_id: int) -> None:
        query = """
            INSERT INTO account_telegram_links (telegram_user_id, account_id)
            VALUES ($1, $2)
        """
        await self._query_executor.execute(query, telegram_user_id, account_id)

    async def backfill_subscriptions_account_id(self, account_id: int, telegram_user_id: int) -> None:
        query = """
            UPDATE subscriptions
            SET account_id = $1, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $2 AND account_id IS NULL
        """
        await self._query_executor.execute(query, account_id, telegram_user_id)
