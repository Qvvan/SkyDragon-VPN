"""Развёрнутые тексты для admin/info-группы (log_info): платежи, подписки, подарки, пробный период."""

from __future__ import annotations

from typing import Any, Optional

from utils.service_ui_label import service_keyboard_label


def payment_lines(payment_response: Any) -> str:
    """Поля из ответа YooKassa (или dict из auto_renewal)."""
    if payment_response is None:
        return ""
    if isinstance(payment_response, dict):
        parts = []
        pid = payment_response.get("id")
        if pid:
            parts.append(f"YooKassa payment_id: {pid}")
        status = payment_response.get("status")
        if status:
            parts.append(f"статус: {status}")
        amt = payment_response.get("amount") or {}
        if isinstance(amt, dict):
            v, c = amt.get("value"), amt.get("currency")
            if v is not None:
                parts.append(f"сумма: {v} {c or 'RUB'}")
        return "\n".join(parts)

    parts = []
    pid = getattr(payment_response, "id", None)
    if pid:
        parts.append(f"YooKassa payment_id: {pid}")
    status = getattr(payment_response, "status", None)
    if status:
        parts.append(f"статус: {status}")
    amt = getattr(payment_response, "amount", None)
    if amt is not None:
        v = getattr(amt, "value", None)
        c = getattr(amt, "currency", None)
        if v is not None:
            parts.append(f"сумма: {v} {c or 'RUB'}")
    pm = getattr(payment_response, "payment_method", None)
    if pm is not None:
        saved = getattr(pm, "saved", None)
        if saved is not None:
            parts.append(f"карта сохранена (автопродление): {saved}")
        pm_id = getattr(pm, "id", None)
        if pm_id:
            parts.append(f"payment_method.id: {pm_id}")
    return "\n".join(parts)


def user_lines(user_id: int, username: Optional[str]) -> str:
    u = (username or "").strip() or "—"
    if u != "—":
        return f"user_id: {user_id}\nusername: @{u}"
    return f"user_id: {user_id}\nusername: —"


def service_lines(service: Any) -> str:
    if service is None:
        return "услуга: нет данных в БД"
    sid = getattr(service, "service_id", None)
    name = getattr(service, "name", "—")
    days = getattr(service, "duration_days", "—")
    price = getattr(service, "price", "—")
    try:
        tariff = service_keyboard_label(int(days), price)
    except Exception:
        tariff = f"{days} дн. — {price} ₽"
    return (
        f"service_id: {sid}\n"
        f"тариф (дни/цена): {tariff}\n"
        f"name в БД (ЮKassa/чеки): {name}"
    )


def admin_activity_message(
    title: str,
    *,
    user_id: int,
    username: Optional[str] = None,
    service: Any = None,
    subscription_id: Optional[int] = None,
    payment_response: Any = None,
    extra: Optional[str] = None,
) -> str:
    blocks = [f"📋 {title}", user_lines(user_id, username)]
    if service is not None:
        blocks.append(service_lines(service))
    if subscription_id is not None and subscription_id != -99999:
        blocks.append(f"subscription_id: {subscription_id}")
    pl = payment_lines(payment_response)
    if pl:
        blocks.append(pl)
    if extra:
        blocks.append(extra.strip())
    return "\n\n".join(blocks)
