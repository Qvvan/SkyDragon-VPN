from typing import Annotated

from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from starlette import status

from src.api.dependencies import get_payment_service
from src.services.payment_service import PaymentService

router = APIRouter(tags=["Payments"])


@router.post("/sub/{encrypted_part}/payments/create", status_code=status.HTTP_303_SEE_OTHER)
async def create_payment_for_renewal(
    encrypted_part: str,
    service_id: Annotated[int, Form()],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)],
):
    redirect_url = await payment_service.create_payment_for_renewal(encrypted_part=encrypted_part, service_id=service_id)
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
