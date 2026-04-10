from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.dependencies import get_telegram_account_link_service, require_bot_api_secret
from src.api.v1.schemas.account import BotTelegramLinkConfirmRequest, BotTelegramLinkConfirmResponse
from src.services.telegram_account_link_service import TelegramAccountLinkService

router = APIRouter(prefix="/internal/bot", tags=["Internal — Bot"])


@router.post(
    "/telegram-link/confirm",
    response_model=BotTelegramLinkConfirmResponse,
    dependencies=[Depends(require_bot_api_secret)],
)
async def confirm_telegram_link(
    data: BotTelegramLinkConfirmRequest,
    link_service: Annotated[TelegramAccountLinkService, Depends(get_telegram_account_link_service)],
):
    account_id = await link_service.confirm_link(code=data.code, telegram_user_id=data.telegram_user_id)
    return BotTelegramLinkConfirmResponse(account_id=account_id)
