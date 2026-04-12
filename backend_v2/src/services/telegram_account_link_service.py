from src.interfaces.repositories.account_telegram_link import IAccountTelegramLinkRepository
from src.interfaces.services.telegram_link_token import ITelegramLinkTokenService


class TelegramAccountLinkService:
    __slots__ = ("_links", "_tokens")

    def __init__(
        self,
        link_repo: IAccountTelegramLinkRepository,
        token_service: ITelegramLinkTokenService,
    ) -> None:
        self._links = link_repo
        self._tokens = token_service

    async def get_linked_telegram_id(self, account_id: str) -> int | None:
        return await self._links.get_telegram_id_by_account(account_id)

    def generate_link_token(self, account_id: str) -> str:
        """Return a Fernet-encrypted token encoding account_id for Telegram ?start= parameter."""
        return self._tokens.generate(account_id)
