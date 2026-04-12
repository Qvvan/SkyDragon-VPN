import asyncpg

from src.domain.entities.account import Account
from src.interfaces.clients.db.query_executor import IQueryExecutor
from src.interfaces.repositories.account import IAccountRepository


class PostgresAccountRepository(IAccountRepository):
    __slots__ = ("_query_executor",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._query_executor = query_executor

    async def create(
        self,
        *,
        login: str,
        password_hash: str,
        first_name: str,
        last_name: str,
    ) -> Account:
        query = """
            INSERT INTO accounts (login, password_hash, first_name, last_name)
            VALUES ($1, $2, $3, $4)
            RETURNING id, login, password_hash, first_name, last_name, created_at, updated_at
        """
        row = await self._query_executor.fetch_row(query, login, password_hash, first_name, last_name)
        if not row:
            msg = "Failed to create account"
            raise RuntimeError(msg)
        return self._row_to_account(row)

    async def get_by_id(self, account_id: str) -> Account | None:
        query = """
            SELECT id, login, password_hash, first_name, last_name, created_at, updated_at
            FROM accounts
            WHERE id = $1
        """
        row = await self._query_executor.fetch_row(query, account_id)
        return self._row_to_account(row) if row else None

    async def get_by_login(self, login: str) -> Account | None:
        query = """
            SELECT id, login, password_hash, first_name, last_name, created_at, updated_at
            FROM accounts
            WHERE login = $1
        """
        row = await self._query_executor.fetch_row(query, login)
        return self._row_to_account(row) if row else None

    async def update_profile(
        self,
        *,
        account_id: str,
        first_name: str | None,
        last_name: str | None,
    ) -> Account:
        query = """
            UPDATE accounts
            SET
                first_name = COALESCE($2, first_name),
                last_name = COALESCE($3, last_name),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
            RETURNING id, login, password_hash, first_name, last_name, created_at, updated_at
        """
        row = await self._query_executor.fetch_row(query, account_id, first_name, last_name)
        if not row:
            msg = "Account not found"
            raise RuntimeError(msg)
        return self._row_to_account(row)

    @staticmethod
    def _row_to_account(row: asyncpg.Record) -> Account:
        return Account(
            id=str(row["id"]),
            login=row["login"],
            first_name=row["first_name"] or "",
            last_name=row["last_name"] or "",
            password_hash=row["password_hash"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
