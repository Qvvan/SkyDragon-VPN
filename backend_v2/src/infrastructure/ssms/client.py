"""Клиент SSMS API для авторизации методом входящего звонка (wait_call)."""

import httpx

from src.domain.entities.types import WaitCallResult, SmsSendResult
from src.core.exceptions import ValidationError
from src.core.logger import AppLogger

from src.interfaces.clients.sms.client import ISmsVerificationClient


class SsmsClient(ISmsVerificationClient):
    """Клиент для вызова SSMS API (wait_call, push_msg)."""

    __slots__ = (
        "_api_key",
        "_api_url",
        "_call_protection_seconds",
        "_email",
        "_http_client",
        "_logger",
        "_password",
    )

    def __init__(
        self,
        *,
        api_url: str,
        email: str,
        password: str,
        api_key: str,
        call_protection_seconds: int,
        logger: AppLogger,
    ) -> None:
        self._api_url = api_url.rstrip("/")
        self._email = email
        self._password = password
        self._api_key = api_key
        self._call_protection_seconds = call_protection_seconds
        self._logger = logger
        self._http_client = httpx.AsyncClient(timeout=30.0)

    @staticmethod
    def _parse_ssms_error_code(msg: dict) -> int:
        """Нормализует err_code из ответа SSMS (может быть str или int)."""
        err_code = msg.get("err_code", 0)
        if isinstance(err_code, str):
            return int(err_code) if err_code.isdigit() else 0
        try:
            return int(err_code)
        except (TypeError, ValueError):
            return 0

    def _raise_if_ssms_error(
        self,
        msg: dict,
        *,
        log_message: str,
        user_message: str,
        default_api_text: str,
    ) -> None:
        err_code = self._parse_ssms_error_code(msg)
        if err_code == 0:
            return
        text = msg.get("text", default_api_text)
        self._logger.warning(log_message, err_code=err_code, text=text)
        raise ValidationError(user_message)

    async def close(self) -> None:
        await self._http_client.aclose()

    async def _post_ssms(self, params: dict[str, str | int]) -> dict:
        """POST form-data: секреты не попадают в query string (логи прокси/сервера)."""
        endpoint = self._api_url + "/"
        form = {k: str(v) for k, v in params.items()}
        resp = await self._http_client.post(endpoint, data=form)
        resp.raise_for_status()
        return resp.json()

    async def wait_call(self, phone: str, hook_url: str) -> WaitCallResult:
        """
        Инициировать ожидание входящего звонка от абонента.
        phone: нормализованный номер (7XXXXXXXXXX).
        hook_url: URL для GET-запроса при поступлении звонка.
        """
        params: dict[str, str | int] = {
            "method": "wait_call",
            "format": "json",
            "phone": phone,
            "call_protection": self._call_protection_seconds,
            "hook_url": hook_url,
        }
        if self._api_key:
            params["key"] = self._api_key
        else:
            params["email"] = self._email
            params["password"] = self._password

        data = await self._post_ssms(params)

        msg = data.get("response", {}).get("msg", {})
        self._raise_if_ssms_error(
            msg,
            log_message=(
                "SSMS wait_call error (см. настройки SSMS: логин/API key, баланс)"
            ),
            user_message=(
                "Сервис проверки номера временно недоступен. Попробуйте позже или обратитесь в поддержку."
            ),
            default_api_text="Ошибка SSMS",
        )

        inner = data.get("response", {}).get("data") or {}
        call_to_number = inner.get("call_to_number") or ""
        id_call = inner.get("id_call") or ""
        waiting_call_from = inner.get("waiting_call_from") or phone
        if not call_to_number or not id_call:
            raise ValidationError("Некорректный ответ от сервиса проверки номера")

        return WaitCallResult(
            call_to_number=call_to_number,
            id_call=id_call,
            waiting_call_from=waiting_call_from,
        )

    async def push_msg(
        self,
        phone: str,
        text: str,
        sender_name: str,
        priority: int | None = None,
        external_id: str | None = None,
    ) -> SmsSendResult:
        """
        Отправить SMS с кодом подтверждения (method=push_msg).
        Используем тот же аккаунт SSMS, что и для wait_call.
        """
        if not sender_name:
            raise ValidationError("Имя отправителя для SMS не настроено")

        params: dict[str, str | int] = {
            "method": "push_msg",
            "format": "json",
            "phone": phone,
            "text": text,
            "sender_name": sender_name,
        }
        if priority is not None:
            params["priority"] = priority
        if external_id is not None:
            params["external_id"] = external_id

        if self._api_key:
            params["key"] = self._api_key
        else:
            params["email"] = self._email
            params["password"] = self._password

        data = await self._post_ssms(params)

        msg = data.get("response", {}).get("msg", {})
        self._raise_if_ssms_error(
            msg,
            log_message="SSMS push_msg error",
            user_message=(
                "Сервис отправки SMS временно недоступен. Попробуйте позже или обратитесь в поддержку."
            ),
            default_api_text="Ошибка SSMS при отправке SMS",
        )

        inner = data.get("response", {}).get("data") or {}
        sms_id = str(inner.get("id") or "")
        credits = inner.get("credits")
        n_raw_sms = inner.get("n_raw_sms")
        sender_name_resp = inner.get("sender_name") or sender_name
        if not sms_id:
            raise ValidationError("Некорректный ответ от сервиса отправки SMS")

        return SmsSendResult(
            id=sms_id,
            sender_name=sender_name_resp,
            credits=float(credits) if isinstance(credits, (int, float)) else None,
            n_raw_sms=int(n_raw_sms) if isinstance(n_raw_sms, (int, float)) else None,
        )
