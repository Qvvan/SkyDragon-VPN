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
    duration_days: int
    price: int


class ServicePlanListResponse(BaseModel):
    services: list[ServicePlanSchema]
