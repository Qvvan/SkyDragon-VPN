import asyncio
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.context_manager import DatabaseContextManager
from logger.logging_config import logger


async def trial_checker(bot: Bot):
    async with DatabaseContextManager() as session_methods:
        try:
            # Получаем всех пользователей
            users = await session_methods.users.get_all_users()
            if not users:
                return

            one_day_ago = datetime.utcnow() - timedelta(days=1)

            for user in users:
                try:
                    # Проверяем, что пользователь зарегистрировался недавно и не использовал пробную подписку
                    if (
                            not user.trial_used
                            and user.created_at
                            and user.created_at <= one_day_ago
                            and not user.reminder_trial_sub
                    ):
                        # Отправляем сообщение пользователю
                        try:
                            await session_methods.users.update_user(user.user_id, reminder_trial_sub=True)
                            await bot.send_message(
                                chat_id=user.user_id,
                                text=(
                                    f"Привет, {user.username or 'друг'}! 😊\n\n"
                                    f"Ты ещё не активировал пробный период? Давай исправим это! 🎉\n"
                                    f"Всего пара кликов — и ты сможешь попробовать всё бесплатно. Мы уверены, тебе понравится!"
                                ),
                                reply_markup=InlineKeyboardMarkup(
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(
                                                text="⚔️ Активировать подписку",
                                                callback_data="activate_trial"
                                            )
                                        ]
                                    ]
                                )
                            )
                        except:
                            pass
                        await logger.info("Отправлено уведомление пользователю о активации пробного периода\n"
                                          f"ID: {user.user_id}\nUsername: @{user.username}")
                except Exception as e:
                    await logger.error("Ошибка отправки уведомления пользователю о активации пробного периода:", e)
                    await logger.log_error(f"Ошибка отправки уведомления пользователю {user.user_id}:", e)

            await session_methods.session.commit()
        except Exception as e:
            await session_methods.session.commit()
            await logger.error("Ошибка в функции trial_checker:", e)
            await logger.log_error("Ошибка в функции trial_checker", e)


async def run_trial_checker(bot: Bot):
    while True:
        try:
            await trial_checker(bot)
        except Exception as e:
            await logger.log_error("Ошибка в цикле run_checker", e)

        await asyncio.sleep(86400)
