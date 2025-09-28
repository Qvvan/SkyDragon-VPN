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

            # Время "день назад" от текущего момента
            one_day_ago = datetime.utcnow() - timedelta(days=1)

            for user in users:
                try:
                    # Проверяем, что:
                    # 1. Пользователь НЕ использовал пробную подписку
                    # 2. У пользователя есть дата регистрации
                    # 3. Пользователь зарегистрировался БОЛЬШЕ дня назад (created_at < one_day_ago)
                    # 4. Ему еще НЕ отправляли напоминание
                    if (
                            not user.trial_used
                            and user.created_at
                            and user.created_at < one_day_ago
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

                            await logger.log_info(
                                f"Отправлено уведомление пользователю о активации пробного периода\n"
                                f"ID: {user.user_id}\n"
                                f"Username: @{user.username}\n"
                                f"Зарегистрирован: {user.created_at}\n"
                                f"Прошло времени: {datetime.utcnow() - user.created_at}"
                            )
                        except Exception as send_error:
                            # Если не удалось отправить сообщение (например, пользователь заблокировал бота)
                            await logger.log_info(
                                f"Не удалось отправить уведомление пользователю {user.user_id}: {send_error}")
                            # Все равно помечаем, что пытались отправить, чтобы не спамить
                            await session_methods.users.update_user(user.user_id, reminder_trial_sub=True)

                except Exception as e:
                    await logger.log_error(f"Ошибка обработки пользователя {user.user_id}:", e)

            await session_methods.session.commit()
        except Exception as e:
            await logger.log_error("Ошибка в функции trial_checker", e)
            try:
                await session_methods.session.rollback()
            except:
                pass


async def run_trial_checker(bot: Bot):
    while True:
        try:
            await trial_checker(bot)
        except Exception as e:
            await logger.log_error("Ошибка в цикле run_trial_checker", e)

        # Спим 24 часа (86400 секунд)
        await asyncio.sleep(86400)