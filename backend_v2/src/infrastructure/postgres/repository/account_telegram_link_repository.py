from src.interfaces.clients.db.query_executor import IQueryExecutor
from src.interfaces.repositories.account_telegram_link import IAccountTelegramLinkRepository


class PostgresAccountTelegramLinkRepository(IAccountTelegramLinkRepository):
    __slots__ = ("_query_executor",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._query_executor = query_executor

    async def get_account_id_by_telegram(self, telegram_user_id: int) -> str | None:
        query = """
            SELECT account_id
            FROM account_telegram_links
            WHERE telegram_user_id = $1
        """
        row = await self._query_executor.fetch_row(query, telegram_user_id)
        return str(row["account_id"]) if row else None

    async def get_telegram_id_by_account(self, account_id: str) -> int | None:
        query = """
            SELECT telegram_user_id
            FROM account_telegram_links
            WHERE account_id = $1
        """
        row = await self._query_executor.fetch_row(query, account_id)
        return int(row["telegram_user_id"]) if row else None

    async def insert_link(self, telegram_user_id: int, account_id: str) -> None:
        query = """
            INSERT INTO account_telegram_links (telegram_user_id, account_id)
            VALUES ($1, $2)
        """
        await self._query_executor.execute(query, telegram_user_id, account_id)

    async def backfill_subscriptions_account_id(self, account_id: str, telegram_user_id: int) -> None:
        query = """
            UPDATE subscriptions
            SET account_id = $1, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $2 AND account_id IS NULL
        """
        await self._query_executor.execute(query, account_id, telegram_user_id)
