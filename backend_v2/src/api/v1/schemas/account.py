from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    login: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=256)
    first_name: str = Field(min_length=1, max_length=128)
    last_name: str = Field(min_length=1, max_length=128)


class LoginRequest(BaseModel):
    login: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AccountPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    login: str
    first_name: str
    last_name: str
    telegram_user_id: int | None = None


class TelegramLinkTokenResponse(BaseModel):
    token: str


class BotTelegramLinkConfirmRequest(BaseModel):
    token: str = Field(min_length=1, max_length=512)
    telegram_user_id: int = Field(gt=0)


class BotTelegramLinkConfirmResponse(BaseModel):
    account_id: UUID


class SubscriptionSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subscription_id: UUID
    user_id: int
    account_id: UUID | None = None
    service_id: int | None
    start_date: datetime | None
    end_date: datetime | None
    status: str | None
    reminder_sent: int
    auto_renewal: bool
    service_name: str | None = None
    service_duration_days: int | None = None
    service_price: int | None = None
    import_url: str | None = None


class SubscriptionSummaryListResponse(BaseModel):
    subscriptions: list[SubscriptionSummarySchema]


class UpdateProfileRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=128)
    last_name: str | None = Field(default=None, min_length=1, max_length=128)


class ToggleAutoRenewalRequest(BaseModel):
    enabled: bool


class PaymentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payment_id: str
    service_id: int | None
    service_name: str | None
    payment_type: str
    status: str
    amount: Decimal
    receipt_link: str | None
    confirmation_url: str | None
    created_at: datetime | None


class PaymentListResponse(BaseModel):
    payments: list[PaymentSchema]


class CreateSubscriptionRequest(BaseModel):
    service_id: int = Field(..., gt=0)


class RenewSubscriptionRequest(BaseModel):
    service_id: int = Field(..., gt=0)


class CreateSubscriptionResponse(BaseModel):
    payment_url: str


class ReferralStatsResponse(BaseModel):
    total_referrals: int = 0
    total_bonus_days: int = 0
    referral_code: str = ""
    referral_link: str = ""


class ReferralSchema(BaseModel):
    id: str
    masked_login: str
    joined_at: str
    bonus_days_granted: int


class ReferralListResponse(BaseModel):
    referrals: list[ReferralSchema] = []


class GiftCodeSchema(BaseModel):
    code: str
    service_id: str
    service_name: str
    duration_days: int
    created_at: str


class CreateGiftRequest(BaseModel):
    service_id: str
    duration_days: int = Field(..., gt=0)


class ActivateGiftRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=64)


class ChatMessageSchema(BaseModel):
    id: str
    role: str
    text: str
    created_at: str


class ChatMessageListResponse(BaseModel):
    messages: list[ChatMessageSchema] = []


class SendChatMessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096)
