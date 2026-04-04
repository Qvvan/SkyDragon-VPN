from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse

from api.dependencies import get_container, get_public_subscription_service
from core.container import Container
from services.public_subscription_service import PublicSubscriptionService
from services.subscription_formatting import (
    happ_add_subscription_deeplink,
    is_browser_request,
    is_known_client_request,
    public_sub_url,
)

router = APIRouter(tags=["subscription"])


def _public_base(container: Container) -> str:
    return (container.config.app.PUBLIC_BASE_URL or "").strip() or "https://skydragonvpn.ru"


@router.get("/sub/{encrypted_part}")
async def get_subscription(
    encrypted_part: str,
    request: Request,
    svc: Annotated[PublicSubscriptionService, Depends(get_public_subscription_service)],
):
    user_agent = request.headers.get("user-agent", "")
    if is_browser_request(user_agent) and not is_known_client_request(user_agent):
        ctx = await svc.build_import_page_context(
            encrypted_part=encrypted_part,
            user_agent=user_agent,
        )
        templates = request.app.state.templates
        return templates.TemplateResponse(
            name="subscription_import.html",
            request=request,
            context=ctx,
        )
    payload = await svc.build_client_subscription_payload(encrypted_part=encrypted_part)
    return Response(content=payload.content_b64, media_type="text/plain; charset=utf-8", headers=payload.headers)


@router.get("/sub/{encrypted_part}/list")
async def get_subscription_list(
    encrypted_part: str,
    svc: Annotated[PublicSubscriptionService, Depends(get_public_subscription_service)],
):
    return await svc.list_subscription_keys_json(encrypted_part=encrypted_part)


@router.post("/sub/{encrypted_part}/auto-renewal/disable")
async def disable_auto_renewal(
    encrypted_part: str,
    svc: Annotated[PublicSubscriptionService, Depends(get_public_subscription_service)],
):
    await svc.disable_auto_renewal(encrypted_part=encrypted_part)
    return RedirectResponse(url=f"/sub/{encrypted_part}", status_code=303)


@router.post("/sub/{encrypted_part}/auto-renewal/enable")
async def enable_auto_renewal(
    encrypted_part: str,
    svc: Annotated[PublicSubscriptionService, Depends(get_public_subscription_service)],
):
    await svc.enable_auto_renewal(encrypted_part=encrypted_part)
    return RedirectResponse(url=f"/sub/{encrypted_part}", status_code=303)


@router.post("/sub/{encrypted_part}/payments/create")
async def create_payment_for_renewal(
    encrypted_part: str,
    service_id: Annotated[int, Form()],
    svc: Annotated[PublicSubscriptionService, Depends(get_public_subscription_service)],
):
    url = await svc.create_renewal_payment_redirect(
        encrypted_part=encrypted_part,
        service_id=service_id,
    )
    return RedirectResponse(url=url, status_code=303)


@router.get("/sub/{encrypted_part}/services")
async def get_renewal_services(
    encrypted_part: str,
    svc: Annotated[PublicSubscriptionService, Depends(get_public_subscription_service)],
):
    services = await svc.list_renewal_services_for_link(encrypted_part=encrypted_part)
    return {"services": services}


@router.get("/import/iphone/{encrypted_part}")
async def import_iphone_legacy(
    encrypted_part: str,
    container: Annotated[Container, Depends(get_container)],
):
    base = _public_base(container)
    return RedirectResponse(url=f"v2raytun://import/{public_sub_url(base, encrypted_part)}", status_code=302)


@router.get("/import/android/{encrypted_part}")
async def import_android_legacy(
    encrypted_part: str,
    container: Annotated[Container, Depends(get_container)],
):
    base = _public_base(container)
    return RedirectResponse(url=f"v2raytun://import/{public_sub_url(base, encrypted_part)}", status_code=302)


@router.get("/import/iphone/happ/{encrypted_part}")
async def import_iphone_happ(
    encrypted_part: str,
    container: Annotated[Container, Depends(get_container)],
):
    return RedirectResponse(url=happ_add_subscription_deeplink(_public_base(container), encrypted_part), status_code=302)


@router.get("/import/android/happ/{encrypted_part}")
async def import_android_happ(
    encrypted_part: str,
    container: Annotated[Container, Depends(get_container)],
):
    return RedirectResponse(url=happ_add_subscription_deeplink(_public_base(container), encrypted_part), status_code=302)


@router.get("/import/android/v2raytun/{encrypted_part}")
async def import_android_v2raytun(
    encrypted_part: str,
    container: Annotated[Container, Depends(get_container)],
):
    base = _public_base(container)
    return RedirectResponse(url=f"v2raytun://import/{public_sub_url(base, encrypted_part)}", status_code=302)


@router.get("/import/iphone/v2raytun/{encrypted_part}")
async def import_iphone_v2raytun(
    encrypted_part: str,
    container: Annotated[Container, Depends(get_container)],
):
    base = _public_base(container)
    return RedirectResponse(url=f"v2raytun://import/{public_sub_url(base, encrypted_part)}", status_code=302)


@router.get("/import/windows/happ/{encrypted_part}")
async def import_windows_happ(
    encrypted_part: str,
    container: Annotated[Container, Depends(get_container)],
):
    return RedirectResponse(url=happ_add_subscription_deeplink(_public_base(container), encrypted_part), status_code=302)


@router.get("/import/windows/v2raytun/{encrypted_part}")
async def import_windows_v2raytun(
    encrypted_part: str,
    container: Annotated[Container, Depends(get_container)],
):
    base = _public_base(container)
    return RedirectResponse(url=f"v2raytun://import/{public_sub_url(base, encrypted_part)}", status_code=302)


@router.get("/import/macos/happ/{encrypted_part}")
async def import_macos_happ(
    encrypted_part: str,
    container: Annotated[Container, Depends(get_container)],
):
    return RedirectResponse(url=happ_add_subscription_deeplink(_public_base(container), encrypted_part), status_code=302)


@router.get("/import/macos/v2raytun/{encrypted_part}")
async def import_macos_v2raytun(
    encrypted_part: str,
    container: Annotated[Container, Depends(get_container)],
):
    base = _public_base(container)
    return RedirectResponse(url=f"v2raytun://import/{public_sub_url(base, encrypted_part)}", status_code=302)
