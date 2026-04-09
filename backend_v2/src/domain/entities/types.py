from dataclasses import dataclass


@dataclass(slots=True)
class WaitCallResult:
    """Результат инициации ожидания звонка."""

    call_to_number: str
    id_call: str
    waiting_call_from: str


@dataclass(slots=True)
class SmsSendResult:
    """Результат отправки SMS (push_msg)."""

    id: str
    sender_name: str
    credits: float | None = None
    n_raw_sms: int | None = None
