from pydantic import BaseModel, Field


class CreatePaymentRequest(BaseModel):
    service_id: int = Field(..., gt=0)
