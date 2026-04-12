import asyncio
import signal
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config_data import config
from database.init_db import get_database
from handlers.admin import add_server, user_info, cancel, pushes, show_servers, get_user_id, \
    add_gift, message_for_user, new_keys, online_abuse_test
from handlers.services import guide_install, trial_subscription
from handlers.services.card_service import payment_status_checker
from handlers.user import start, support, createorder, online_users_vpn, legend
from handlers.user import subs, referrer, menu, just_message, gift_sub, \
    send_stikers, history_payments
from logger.logging_config import logger
from middleware.logging_middleware import CallbackLoggingMiddleware, MessageLoggingMiddleware
from middleware.trottling import ThrottlingMiddleware
from scripts import update_keys
from utils.check_servers import ping_servers
from utils.gift_checker import run_gift_checker
from utils.online_abuse_checker import run_online_abuse_check
from utils.subscription_checker import run_checker
from utils.trial_checker import run_trial_checker
from workers.key_operations_worker import run_key_operations_worker

# Глобальные переменные для контроля
bot_instance = None
dp_instance = None
background_tasks = []
is_shutting_down = False


def normalize_telegram_proxy(proxy: str) -> str:
    """
    Приводим прокси к формату, который ожидает aiogram/AiohttpSession.
    Поддерживаем ввод как `ip:port` (автопрефикс `socks5://`) или полный URL.
    """
    proxy = (proxy or "").strip()
    if not proxy:
        return ""
    if "://" not in proxy:
        return f"socks5://{proxy}"
    return proxy


async def cleanup_bot_resources():
    """Очистка ресурсов бота."""
    global bot_instance, dp_instance, background_tasks, is_shutting_down

    is_shutting_down = True

    for task in background_tasks:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    background_tasks.clear()

    # Закрываем сессию бота
    if bot_instance and bot_instance.session:
        await bot_instance.session.close()


def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения."""
    print(f"\nПолучен сигнал {signum}. Завершение работы...")
    sys.exit(0)


async def on_startup(bot: Bot):
    """Оповещение администраторов о запуске бота."""
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🟢 Бот запущен.")
        except Exception as e:
            await logger.log_error(f"Ошибка отправки сообщения администратору {admin_id}", e)


async def on_shutdown(bot: Bot):
    """Оповещение администраторов о завершении работы бота."""
    if not is_shutting_down:
        for admin_id in config.ADMIN_IDS:
            try:
                await bot.send_message(admin_id, "🔴 Бот завершает работу.")
            except Exception as e:
                await logger.log_error(f"Ошибка отправки сообщения администратору {admin_id}", e)


def setup_routers(dp: Dispatcher):
    """Настройка роутеров для диспетчера."""
    # Проверяем, не подключены ли уже роутеры
    routers_to_include = [
        user_info.router,
        legend.router,
        send_stikers.router,
        history_payments.router,
        cancel.router,
        menu.router,
        createorder.router,
        subs.router,
        start.router,
        support.router,
        guide_install.router,
        referrer.router,
        trial_subscription.router,
        gift_sub.router,
        update_keys.router,
        online_users_vpn.router,
        new_keys.router,
        add_server.router,
        pushes.router,
        show_servers.router,
        online_abuse_test.router,
        get_user_id.router,
        add_gift.router,
        message_for_user.router,
        just_message.router
    ]

    for router in routers_to_include:
        # Отключаем роутер от предыдущего диспетчера если нужно
        if router.parent_router is not None:
            router.parent_router = None

        dp.include_router(router)


async def setup_background_tasks(bot: Bot):
    """Запуск фоновых задач."""
    global background_tasks

    # Отменяем старые задачи если есть
    for task in background_tasks:
        if not task.done():
            task.cancel()

    background_tasks.clear()

    # Создаем новые задачи
    background_tasks.extend([
        asyncio.create_task(run_checker(bot)),
        asyncio.create_task(ping_servers(bot)),
        asyncio.create_task(payment_status_checker(bot)),
        asyncio.create_task(run_trial_checker(bot)),
        asyncio.create_task(run_gift_checker(bot)),
        asyncio.create_task(run_online_abuse_check(bot)),
        # key_operations_worker disabled — backend_v2 handles key provisioning
        # asyncio.create_task(run_key_operations_worker()),
    ])


async def create_bot_instance():
    """Создание нового экземпляра бота и диспетчера."""
    global bot_instance, dp_instance

    # Очищаем предыдущие экземпляры
    if bot_instance and bot_instance.session:
        await bot_instance.session.close()

    # Создаем базу данных (используем singleton)
    db = get_database()
    await db.create_db()

    # Создаем новые экземпляры
    storage = MemoryStorage()

    telegram_proxy = normalize_telegram_proxy(config.TELEGRAM_PROXY)
    session = AiohttpSession(proxy=telegram_proxy or None)

    bot_instance = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )

    dp_instance = Dispatcher(storage=storage)

    # Настраиваем middleware
    dp_instance.message.outer_middleware(MessageLoggingMiddleware())
    dp_instance.callback_query.outer_middleware(CallbackLoggingMiddleware())

    throttling_middleware = ThrottlingMiddleware(limit=0.3)
    dp_instance.message.outer_middleware(throttling_middleware)
    dp_instance.callback_query.outer_middleware(throttling_middleware)

    # Регистрируем события
    dp_instance.startup.register(on_startup)
    dp_instance.shutdown.register(on_shutdown)

    # Настраиваем роутеры
    setup_routers(dp_instance)

    return bot_instance, dp_instance


async def main():
    """Основная функция бота."""
    global bot_instance, dp_instance, is_shutting_down

    await logger.info('🚀 Starting bot')

    try:
        # Создаем экземпляры бота и диспетчера
        bot, dp = await create_bot_instance()

        # Запускаем фоновые задачи
        await setup_background_tasks(bot)

        # Удаляем webhook с увеличенным таймаутом
        try:
            await bot.delete_webhook(drop_pending_updates=True, request_timeout=30)
        except Exception as e:
            await logger.error("Ошибка при удалении webhook", e)
            # Продолжаем работу даже если не удалось удалить webhook

        # Запускаем polling
        await logger.info('✅ Bot started successfully')
        await dp.start_polling(bot, handle_signals=False)

    except Exception as e:
        await logger.error("Критическая ошибка в main()", e)
        raise
    finally:
        if not is_shutting_down:
            await cleanup_bot_resources()


async def run_bot():
    """Функция для запуска бота с автоматическим перезапуском."""
    restart_count = 0
    max_restarts = 10  # Максимальное количество перезапусков подряд
    base_delay = 5

    # Устанавливаем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while restart_count < max_restarts:
        try:
            await main()
            # Если добрались сюда без ошибок, сбрасываем счетчик
            restart_count = 0

        except KeyboardInterrupt:
            await logger.info("🛑 Получен сигнал прерывания. Завершение работы...")
            break

        except Exception as e:
            restart_count += 1
            delay = min(base_delay * restart_count, 60)  # Максимум 60 секунд

            await logger.error(f"💥 Бот завершил работу с ошибкой (попытка {restart_count}/{max_restarts})", e)

            if restart_count >= max_restarts:
                await logger.error("❌ Превышено максимальное количество перезапусков. Завершение работы.", None)
                break

            await logger.info(f"🔄 Перезапуск бота через {delay} секунд...")
            await asyncio.sleep(delay)

    # Финальная очистка
    await cleanup_bot_resources()
    await logger.info("🏁 Бот полностью завершил работу")


if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("Программа прервана пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")