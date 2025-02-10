import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config_data import config
from database.init_db import DataBase
from handlers.admin import add_server, user_info, cancel, refund, help_info, pushes, show_servers, get_user_id, \
    add_gift, message_for_user
from handlers.services import payments_service, guide_install, trial_subscription
from handlers.services.card_service import payment_status_checker
from handlers.user import start, support, createorder
from handlers.user import subs, replace_server, replace_app, referrer, menu, just_message, stars, gift_sub, \
    send_stikers, history_payments
from logger.logging_config import logger
from middleware.logging_middleware import CallbackLoggingMiddleware, MessageLoggingMiddleware
from middleware.trottling import ThrottlingMiddleware
from utils import check_servers
from utils.check_servers import ping_servers
from utils.gift_checker import run_gift_checker
from utils.subscription_checker import run_checker
from utils.trial_checker import run_trial_checker


async def on_startup(bot: Bot):
    """Оповещение администраторов о запуске бота."""
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "Бот запущен.")
        except Exception as e:
            await logger.log_error(f"Ошибка отправки сообщения администратору {admin_id}", e)


async def on_shutdown(bot: Bot):
    """Оповещение администраторов о завершении работы бота."""
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "Бот завершает работу.")
        except Exception as e:
            await logger.log_error(f"Ошибка отправки сообщения администратору {admin_id}", e)


async def main():
    await logger.info('Starting bot')

    db = DataBase()
    await db.create_db()

    storage = MemoryStorage()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=storage)

    dp.message.outer_middleware(MessageLoggingMiddleware())
    dp.callback_query.outer_middleware(CallbackLoggingMiddleware())

    throttling_middleware = ThrottlingMiddleware(limit=0.3)
    dp.message.outer_middleware(throttling_middleware)
    dp.callback_query.outer_middleware(throttling_middleware)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.include_router(user_info.router)
    # user-handlers
    dp.include_router(send_stikers.router)
    dp.include_router(history_payments.router)
    dp.include_router(cancel.router)
    dp.include_router(menu.router)
    dp.include_router(createorder.router)
    dp.include_router(subs.router)
    dp.include_router(start.router)
    dp.include_router(support.router)
    dp.include_router(payments_service.router)
    dp.include_router(replace_server.router)
    dp.include_router(replace_app.router)
    dp.include_router(guide_install.router)
    dp.include_router(referrer.router)
    dp.include_router(trial_subscription.router)
    dp.include_router(stars.router)
    dp.include_router(gift_sub.router)

    # admin-handlers
    dp.include_router(add_server.router)
    dp.include_router(help_info.router)
    dp.include_router(refund.router)
    dp.include_router(pushes.router)
    dp.include_router(check_servers.router)
    dp.include_router(show_servers.router)
    dp.include_router(get_user_id.router)
    dp.include_router(add_gift.router)
    dp.include_router(message_for_user.router)

    dp.include_router(just_message.router)

    asyncio.create_task(run_checker(bot))
    asyncio.create_task(ping_servers(bot))
    asyncio.create_task(payment_status_checker(bot))
    asyncio.create_task(run_trial_checker(bot))
    asyncio.create_task(run_gift_checker(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


async def run_bot():
    while True:
        try:
            await main()
        except Exception as e:
            await logger.error(f"Бот завершил работу с ошибкой", e)
            await logger.info("Перезапуск бота через 5 секунд...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_bot())
