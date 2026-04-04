from domain.entities.push_log import PushLog
from interfaces.clients.db.query_executor import IQueryExecutor
from interfaces.repositories.push_log_repository import IPushLogRepository


class PostgresPushLogRepository(IPushLogRepository):
    __slots__ = ("_qe",)

    def __init__(self, query_executor: IQueryExecutor) -> None:
        self._qe = query_executor

    async def insert(self, *, message: str, user_ids: list[int]) -> PushLog:
        q = """
            INSERT INTO pushes (message, user_ids, timestamp)
            VALUES ($1, $2::bigint[], NOW())
            RETURNING id, message, user_ids, timestamp
        """
        row = await self._qe.fetch_row(q, message, user_ids)
        assert row is not None
        uids = row["user_ids"]
        if uids is not None and not isinstance(uids, list):
            uids = list(uids)
        return PushLog(
            id=row["id"],
            message=row["message"],
            user_ids=list(uids or []),
            timestamp=row.get("timestamp"),
        )
