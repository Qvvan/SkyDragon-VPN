import secrets
from datetime import datetime, timedelta, timezone

from src.core.exceptions import ConflictError, ValidationError
from src.interfaces.repositories.account_telegram_link import IAccountTelegramLinkRepository


class TelegramAccountLinkService:
    __slots__ = ("_links",)

    def __init__(self, link_repo: IAccountTelegramLinkRepository) -> None:
        self._links = link_repo

    async def get_linked_telegram_id(self, account_id: int) -> int | None:
        return await self._links.get_telegram_id_by_account(account_id)

    async def issue_link_code(self, account_id: int) -> tuple[str, datetime]:
        code = _generate_numeric_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        await self._links.replace_link_code(account_id, code, expires_at)
        return code, expires_at

    async def confirm_link(self, code: str, telegram_user_id: int) -> int:
        if telegram_user_id <= 0:
            raise ValidationError("Некорректный telegram_user_id")
        cleaned = code.strip().replace(" ", "")
        if not cleaned:
            raise ValidationError("Код не указан")

        account_id = await self._links.peek_valid_link_code(cleaned)
        if account_id is None:
            raise ValidationError("Код недействителен или истёк")

        existing_acc = await self._links.get_account_id_by_telegram(telegram_user_id)
        if existing_acc is not None:
            raise ConflictError("Этот Telegram уже привязан к другому аккаунту")

        existing_tg = await self._links.get_telegram_id_by_account(account_id)
        if existing_tg is not None:
            raise ConflictError("К этому аккаунту уже привязан другой Telegram")

        taken = await self._links.take_valid_link_code(cleaned)
        if taken != account_id:
            raise ValidationError("Код недействителен или истёк")

        await self._links.insert_link(telegram_user_id, account_id)
        await self._links.backfill_subscriptions_account_id(account_id, telegram_user_id)
        return account_id


def _generate_numeric_code() -> str:
    for _ in range(20):
        code = f"{secrets.randbelow(1_000_000):06d}"
        if code != "000000":
            return code
    return "918273"
