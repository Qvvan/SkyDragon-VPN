"""
Проверка онлайна по подпискам: собирает со всех серверов список онлайн-клиентов,
для каждого запрашивает IP (clientIps), группирует по подписке (user_id, sub_id).
Если по одной подписке онлайн больше чем MAX_CONNECTIONS_PER_SUBSCRIPTION — уведомление админам.
"""
import asyncio
import base64
from dataclasses import dataclass, field
from typing import Any

from aiogram import Bot

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from handlers.services.panel_gateway import PanelGateway
from logger.logging_config import logger

# Лимит: если ключей (подключений) по одной подписке больше этого — шлём алерт
MAX_CONNECTIONS_PER_SUBSCRIPTION = 2

# Интервал между проверками (секунды)
CHECK_INTERVAL_SEC = 5 * 60  # 5 минут


@dataclass
class OnlineEntry:
    """Один онлайн-ключ на одном сервере."""
    server_ip: str
    server_name: str
    client_id: str
    ips: list[str] = field(default_factory=list)


@dataclass
class SubscriptionOnline:
    """Агрегат по подписке: владелец, подписка, список подключений."""
    user_id: int
    sub_id: int
    entries: list[OnlineEntry] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.entries)

    @property
    def total_ips(self) -> int:
        return sum(len(e.ips) for e in self.entries)

    @property
    def server_names(self) -> list[str]:
        return list(dict.fromkeys(e.server_name for e in self.entries))

    @property
    def server_ips(self) -> list[str]:
        return list(dict.fromkeys(e.server_ip for e in self.entries))


def parse_client_id_to_subscription(client_id: str) -> tuple[int, int] | None:
    """
    Парсит client_id из панели (email вида base64(user_id,sub_id|checksum)_portNNNN).
    Возвращает (user_id, sub_id) или None при ошибке.
    """
    try:
        if "_port" not in client_id:
            return None
        base_part = client_id.split("_port")[0].strip()
        if not base_part:
            return None
        decoded = base64.b64decode(base_part).decode("utf-8")
        # формат: "323993202,1|10057b78"
        left = decoded.split("|")[0].strip()
        if "," not in left:
            return None
        parts = left.split(",", 1)
        user_id = int(parts[0].strip())
        sub_id = int(parts[1].strip())
        return (user_id, sub_id)
    except Exception:
        return None


async def collect_online_per_server(server: Any, gateway: PanelGateway) -> list[tuple[str, list[str]]]:
    """
    По одному серверу: получает onlines, для каждого client_id запрашивает clientIps.
    Возвращает список (client_id, ips) для этого сервера.
    """
    result: list[tuple[str, list[str]]] = []
    onlines_data = await gateway.get_online_users()
    if not onlines_data or not onlines_data.get("success"):
        return result
    obj = onlines_data.get("obj")
    if not isinstance(obj, list):
        return result
    for client_id in obj:
        if not isinstance(client_id, str):
            continue
        ips = await gateway.get_client_ips(client_id)
        result.append((client_id, ips))
        await asyncio.sleep(0.05)
    return result


async def collect_all_online_data() -> dict[tuple[int, int], SubscriptionOnline]:
    """
    Собирает онлайны со всех серверов и группирует по подписке (user_id, sub_id).
    Возвращает словарь подписка -> SubscriptionOnline. Можно вызывать для тестов без бота.
    """
    by_sub: dict[tuple[int, int], SubscriptionOnline] = {}

    async with DatabaseContextManager() as session_methods:
        try:
            servers = await session_methods.servers.get_all_servers()
        except Exception as e:
            await logger.log_error("Не удалось получить список серверов для проверки онлайна", e)
            return by_sub

        for server in servers:
            if server.hidden == 1:
                continue
            gateway = PanelGateway(server)
            try:
                pairs = await collect_online_per_server(server, gateway)
                for client_id, ips in pairs:
                    parsed = parse_client_id_to_subscription(client_id)
                    if parsed is None:
                        continue
                    user_id, sub_id = parsed
                    key = (user_id, sub_id)
                    if key not in by_sub:
                        by_sub[key] = SubscriptionOnline(user_id=user_id, sub_id=sub_id)
                    by_sub[key].entries.append(
                        OnlineEntry(
                            server_ip=server.server_ip,
                            server_name=server.name or server.server_ip,
                            client_id=client_id,
                            ips=ips,
                        )
                    )
            except Exception as e:
                await logger.log_error(
                    f"Ошибка при сборе онлайна с сервера {server.server_ip} ({server.name})", e
                )
            finally:
                await gateway.close()

    return by_sub


async def run_online_abuse_check(bot: Bot) -> None:
    """
    Фоновая задача: раз в CHECK_INTERVAL_SEC обходит серверы, собирает онлайны и IP,
    группирует по подписке (user_id, sub_id). Если по подписке ключей > MAX — шлёт уведомление админам.
    """
    while True:
        try:
            await _do_one_check(bot)
        except asyncio.CancelledError:
            break
        except Exception as e:
            await logger.log_error("Ошибка в run_online_abuse_check", e)
        await asyncio.sleep(CHECK_INTERVAL_SEC)


async def _do_one_check(bot: Bot) -> None:
    by_sub = await collect_all_online_data()

    for (user_id, sub_id), sub_online in by_sub.items():
        if sub_online.total_keys <= MAX_CONNECTIONS_PER_SUBSCRIPTION:
            continue
        message = _format_abuse_message(sub_online)
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, message)
            except Exception as e:
                await logger.log_error(f"Не удалось отправить уведомление о нарушении админу {admin_id}", e)


def _format_abuse_message(sub: SubscriptionOnline) -> str:
    lines = [
        "⚠️ <b>Превышен лимит подключений по подписке</b>",
        "",
        f"Подписка: <code>user_id={sub.user_id}, sub_id={sub.sub_id}</code>",
        f"Telegram ID владельца: <code>{sub.user_id}</code>",
        f"Всего ключей онлайн: <b>{sub.total_keys}</b> (лимит {MAX_CONNECTIONS_PER_SUBSCRIPTION})",
        f"Всего IP-адресов: {sub.total_ips}",
        f"Серверы: {', '.join(sub.server_names)}",
        "",
        "Подключения по серверам:",
    ]
    for entry in sub.entries:
        ips_str = ", ".join(entry.ips) if entry.ips else "—"
        lines.append(f"  • {entry.server_name} ({entry.server_ip}): ключ {entry.client_id[:40]}… — IP: {ips_str}")
    return "\n".join(lines)
