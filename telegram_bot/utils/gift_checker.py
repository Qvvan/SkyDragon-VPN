import asyncio
from datetime import datetime

from aiogram import Bot

from database.context_manager import DatabaseContextManager
from handlers.services.extend_latest_subscription import extend_user_subscription
from logger.logging_config import logger
from models.models import Gifts


async def gift_checker(bot: Bot):
    async with DatabaseContextManager() as session_methods:
        try:
            gifts = await session_methods.gifts.get_pending_gifts()
            for gift in gifts:
                try:
                    user = await session_methods.users.get_user_by_username(gift.receiver_username)
                    giver = await session_methods.users.get_user(gift.giver_id)
                    if user:
                        service = await session_methods.services.get_service_by_id(gift.service_id)
                        await session_methods.gifts.update_gift(
                            gift_id=gift.gift_id,
                            status="used",
                            activated_at=datetime.utcnow()
                        )
                        await extend_user_subscription(user.user_id, gift.receiver_username, service.duration_days,
                                                       session_methods)
                        await bot.send_message(giver.user_id,
                                               f"🎁 Ваш друг @{gift.receiver_username} успешно получил ваш подарок после регистрации! ✨")
                        await bot.send_message(user.user_id,
                                               f"🎁 Вам подарок! 🎉\n\n"
                                               f"Ваш друг {'@' + giver.username if giver.username else 'Неизвестный пользователь'} решил сделать вам приятный сюрприз! ✨\n\n"
                                               f"💪 Защита {service.name}а на {service.duration_days} дней 🛡️\n\n"
                                               f"🌐 Подписка уже активирована, для большей информации зайдите в /profile 🔒"
                                               )
                        await logger.log_info(
                            f"Пользователь: @{gift.receiver_username}\n"
                            f"Получил подарок от пользователя: @{giver.username}\n"
                            f"Подарок: {service.name} на {service.duration_days} дней"
                        )
                except Exception as e:
                    await logger.log_error(f'Ошибка при выдачи подарка', e)
            await session_methods.session.commit()
        except Exception as e:
            await logger.log_error(f'Ошибка при получении списка подарков', e)
            return


async def run_gift_checker(bot: Bot):
    while True:
        try:
            await gift_checker(bot)
        except Exception as e:
            await logger.log_error("Ошибка в цикле run_checker", e)

        await asyncio.sleep(10)
