from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SubscriptionListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    keys: list[str]
    servers: list[dict[str, str]]
    message: str | None = None


class ServicePlanSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    service_id: int
    name: str
    description: str | None
    duration_days: int
    price: int
    original_price: int | None
    is_trial: bool
    is_featured: bool
    badge: str | None


class ServicePlanListResponse(BaseModel):
    services: list[ServicePlanSchema]


class TrialActivatedResponse(BaseModel):
    subscription_id: UUID
    end_date: str
