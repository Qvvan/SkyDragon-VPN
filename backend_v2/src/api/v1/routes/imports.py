from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from starlette import status

from src.api.dependencies import get_import_service
from src.services.import_service import ImportService

router = APIRouter(tags=["Import"])


@router.get("/import/{platform}/{encrypted_part}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def import_legacy(
    platform: str,
    encrypted_part: str,
    import_service: Annotated[ImportService, Depends(get_import_service)],
):
    target_url = import_service.route_deeplink(platform=platform, app_name="happ", encrypted_part=encrypted_part)
    return RedirectResponse(url=target_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/import/{platform}/{app_name}/{encrypted_part}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def import_platform_app(
    platform: str,
    app_name: str,
    encrypted_part: str,
    import_service: Annotated[ImportService, Depends(get_import_service)],
):
    target_url = import_service.route_deeplink(platform=platform, app_name=app_name, encrypted_part=encrypted_part)
    return RedirectResponse(url=target_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
