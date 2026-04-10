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
        email: str | None,
        phone: str | None,
        password_hash: str,
        first_name: str,
        last_name: str,
    ) -> Account:
        query = """
            INSERT INTO accounts (email, phone, password_hash, first_name, last_name)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, email, phone, password_hash, first_name, last_name, created_at, updated_at
        """
        row = await self._query_executor.fetch_row(query, email, phone, password_hash, first_name, last_name)
        if not row:
            msg = "Failed to create account"
            raise RuntimeError(msg)
        return self._row_to_account(row)

    async def get_by_id(self, account_id: int) -> Account | None:
        query = """
            SELECT id, email, phone, password_hash, first_name, last_name, created_at, updated_at
            FROM accounts
            WHERE id = $1
        """
        row = await self._query_executor.fetch_row(query, account_id)
        return self._row_to_account(row) if row else None

    async def get_by_email_lower(self, email_lower: str) -> Account | None:
        query = """
            SELECT id, email, phone, password_hash, first_name, last_name, created_at, updated_at
            FROM accounts
            WHERE LOWER(email) = $1
        """
        row = await self._query_executor.fetch_row(query, email_lower)
        return self._row_to_account(row) if row else None

    async def get_by_phone(self, phone: str) -> Account | None:
        query = """
            SELECT id, email, phone, password_hash, first_name, last_name, created_at, updated_at
            FROM accounts
            WHERE phone = $1
        """
        row = await self._query_executor.fetch_row(query, phone)
        return self._row_to_account(row) if row else None

    @staticmethod
    def _row_to_account(row: asyncpg.Record) -> Account:
        return Account(
            id=row["id"],
            email=row["email"],
            phone=row["phone"],
            first_name=row["first_name"] or "",
            last_name=row["last_name"] or "",
            password_hash=row["password_hash"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
