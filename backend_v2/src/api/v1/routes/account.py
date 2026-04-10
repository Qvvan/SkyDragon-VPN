from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.dependencies import get_current_account, get_subscription_service, get_telegram_account_link_service
from src.api.v1.schemas.account import (
    AccountPublicSchema,
    SubscriptionSummaryListResponse,
    SubscriptionSummarySchema,
    TelegramLinkCodeResponse,
)
from src.domain.entities.account import Account
from src.services.subscription_service import SubscriptionService
from src.services.telegram_account_link_service import TelegramAccountLinkService

router = APIRouter(prefix="/me", tags=["Me"])


@router.get("", response_model=AccountPublicSchema)
async def get_me(
    account: Annotated[Account, Depends(get_current_account)],
    link_service: Annotated[TelegramAccountLinkService, Depends(get_telegram_account_link_service)],
):
    tg = await link_service.get_linked_telegram_id(account.id)
    return AccountPublicSchema(
        id=account.id,
        email=account.email,
        phone=account.phone,
        first_name=account.first_name,
        last_name=account.last_name,
        telegram_user_id=tg,
    )


@router.get("/subscriptions", response_model=SubscriptionSummaryListResponse)
async def list_my_subscriptions(
    account: Annotated[Account, Depends(get_current_account)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    rows = await subscription_service.list_subscriptions_for_account(account.id)
    return SubscriptionSummaryListResponse(
        subscriptions=[SubscriptionSummarySchema.model_validate(s, from_attributes=True) for s in rows],
    )


@router.post("/telegram/link-code", response_model=TelegramLinkCodeResponse)
async def create_telegram_link_code(
    account: Annotated[Account, Depends(get_current_account)],
    link_service: Annotated[TelegramAccountLinkService, Depends(get_telegram_account_link_service)],
):
    code, expires_at = await link_service.issue_link_code(account.id)
    return TelegramLinkCodeResponse(code=code, expires_at=expires_at)
