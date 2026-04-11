from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from src.api.dependencies import (
    get_auth_service,
    get_current_account,
    get_payment_service,
    get_subscription_service,
    get_telegram_account_link_service,
)
from src.api.v1.schemas.account import (
    AccountPublicSchema,
    ActivateGiftRequest,
    ChatMessageListResponse,
    ChatMessageSchema,
    CreateGiftRequest,
    CreateSubscriptionRequest,
    CreateSubscriptionResponse,
    GiftCodeSchema,
    PaymentListResponse,
    PaymentSchema,
    ReferralListResponse,
    ReferralStatsResponse,
    SendChatMessageRequest,
    SubscriptionSummaryListResponse,
    SubscriptionSummarySchema,
    TelegramLinkCodeResponse,
    ToggleAutoRenewalRequest,
    UpdateProfileRequest,
)
from src.domain.entities.account import Account
from src.services.auth_service import AuthService
from src.services.payment_service import PaymentService
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


@router.patch("", response_model=AccountPublicSchema)
async def update_profile(
    data: UpdateProfileRequest,
    account: Annotated[Account, Depends(get_current_account)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    link_service: Annotated[TelegramAccountLinkService, Depends(get_telegram_account_link_service)],
):
    updated = await auth_service.update_profile(
        account.id,
        first_name=data.first_name,
        last_name=data.last_name,
    )
    tg = await link_service.get_linked_telegram_id(updated.id)
    return AccountPublicSchema(
        id=updated.id,
        email=updated.email,
        phone=updated.phone,
        first_name=updated.first_name,
        last_name=updated.last_name,
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


@router.patch("/subscriptions/{subscription_id}/auto-renewal", status_code=status.HTTP_204_NO_CONTENT)
async def toggle_auto_renewal(
    subscription_id: int,
    data: ToggleAutoRenewalRequest,
    account: Annotated[Account, Depends(get_current_account)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
):
    await subscription_service.set_auto_renewal_for_account(account.id, subscription_id, data.enabled)


@router.post("/subscriptions", response_model=CreateSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    data: CreateSubscriptionRequest,
    account: Annotated[Account, Depends(get_current_account)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
):
    payment_url = await payment_service.create_payment_for_account(account.id, data.service_id)
    return CreateSubscriptionResponse(payment_url=payment_url)


@router.get("/payments", response_model=PaymentListResponse)
async def list_my_payments(
    account: Annotated[Account, Depends(get_current_account)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
):
    payments = await payment_service.list_payments_for_account(account.id)
    return PaymentListResponse(
        payments=[PaymentSchema.model_validate(p, from_attributes=True) for p in payments],
    )


@router.post("/telegram/link-code", response_model=TelegramLinkCodeResponse)
async def create_telegram_link_code(
    account: Annotated[Account, Depends(get_current_account)],
    link_service: Annotated[TelegramAccountLinkService, Depends(get_telegram_account_link_service)],
):
    code, expires_at = await link_service.issue_link_code(account.id)
    return TelegramLinkCodeResponse(code=code, expires_at=expires_at)


@router.get("/referrals/stats", response_model=ReferralStatsResponse)
async def get_referral_stats(
    account: Annotated[Account, Depends(get_current_account)],
):
    return ReferralStatsResponse(
        total_referrals=0,
        total_bonus_days=0,
        referral_code="",
        referral_link="",
    )


@router.get("/referrals", response_model=ReferralListResponse)
async def list_referrals(
    account: Annotated[Account, Depends(get_current_account)],
):
    return ReferralListResponse(referrals=[])


@router.post("/gifts", response_model=GiftCodeSchema, status_code=status.HTTP_201_CREATED)
async def create_gift(
    data: CreateGiftRequest,
    account: Annotated[Account, Depends(get_current_account)],
):
    from src.core.exceptions import ValidationError
    raise ValidationError("Функция подарков пока не доступна")


@router.post("/gifts/activate", response_model=GiftCodeSchema)
async def activate_gift(
    data: ActivateGiftRequest,
    account: Annotated[Account, Depends(get_current_account)],
):
    from src.core.exceptions import ValidationError
    raise ValidationError("Функция подарков пока не доступна")


@router.get("/chat/messages", response_model=ChatMessageListResponse)
async def list_chat_messages(
    account: Annotated[Account, Depends(get_current_account)],
):
    return ChatMessageListResponse(messages=[])


@router.post("/chat/messages", response_model=ChatMessageSchema, status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    data: SendChatMessageRequest,
    account: Annotated[Account, Depends(get_current_account)],
):
    import uuid
    from datetime import datetime, timezone
    return ChatMessageSchema(
        id=str(uuid.uuid4()),
        role="support",
        text="Спасибо за сообщение. Мы ответим вам в ближайшее время.",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
