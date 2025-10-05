import asyncio
from datetime import datetime

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database.context_manager import DatabaseContextManager
from handlers.services.extend_latest_subscription import extend_user_subscription
from logger.logging_config import logger


async def gift_checker(bot: Bot):
    async with DatabaseContextManager() as session_methods:
        try:
            gifts = await session_methods.gifts.get_pending_gifts()
            for gift in gifts:
                try:
                    recipient_user = await session_methods.users.get_user(gift.recipient_user_id)
                    sender_user = await session_methods.users.get_user(gift.giver_id)
                    if recipient_user:
                        service = await session_methods.services.get_service_by_id(gift.service_id)

                        await session_methods.gifts.update_gift(
                            gift_id=gift.gift_id,
                            status="awaiting_activation",
                            activated_at=None
                        )

                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(
                                text="🎁 Активировать подарок",
                                callback_data=f"activate_gift_{gift.gift_id}"
                            )]
                        ])
                        await bot.send_message(
                            recipient_user.user_id,
                            f"🎁 Вам подарок! 🎉\n\n"
                            f"Ваш друг {'@' + sender_user.username if sender_user.username else 'Неизвестный пользователь'} решил сделать вам приятный сюрприз! ✨\n\n"
                            f"💪 Защита {service.name} на {service.duration_days} дней 🛡️\n\n"
                            f"Нажмите кнопку ниже, чтобы активировать подарок 👇",
                            reply_markup=keyboard
                        )

                        await logger.log_info(
                            f"Пользователю @{recipient_user.username} отправлен подарок от @{sender_user.username} для активации"
                        )
                except Exception as e:
                    await logger.log_error(f'Ошибка при отправке подарка', e)
            await session_methods.session.commit()
        except Exception as e:
            await logger.log_error(f'Ошибка при получении списка подарков', e)
            return


async def activate_gift_handler(bot: Bot, callback_query: CallbackQuery, gift_id: int):
    """
    Обработчик активации подарка по кнопке
    Этот метод нужно добавить в ваш основной обработчик callback'ов
    """
    async with DatabaseContextManager() as session_methods:
        try:
            # Получаем подарок
            gift = await session_methods.gifts.get_gift_by_id(gift_id)
            recipient_user = await session_methods.users.get_user(gift.recipient_user_id)

            if not gift:
                await callback_query.answer("❌ Подарок не найден", show_alert=True)
                return

            if gift.status != "awaiting_activation":
                await callback_query.answer("❌ Этот подарок уже активирован или недоступен", show_alert=True)
                return

            if callback_query.from_user.id != gift.recipient_user_id:
                await callback_query.answer("❌ Вы не можете активировать этот подарок", show_alert=True)
                return

            # Получаем информацию о сервисе и дарителе
            service = await session_methods.services.get_service_by_id(gift.service_id)
            giver = await session_methods.users.get_user(gift.giver_id)

            service_name = service.name
            service_duration = service.duration_days
            receiver_username = recipient_user.username
            recipient_user_id = recipient_user.user_id
            giver_username = giver.username if giver else 'Unknown'
            giver_user_id = giver.user_id if giver else None

            # Активируем подарок
            await session_methods.gifts.update_gift(
                gift_id=gift.gift_id,
                status="used",
                activated_at=datetime.utcnow()
            )

            # Продлеваем подписку
            await extend_user_subscription(
                gift.recipient_user_id,
                recipient_user.username,
                service.duration_days,
                session_methods
            )

            # Уведомляем получателя об успешной активации
            await callback_query.message.edit_text(
                f"✅ Подарок успешно активирован! 🎉\n\n"
                f"💪 Защита {service.name} на {service.duration_days} дней активирована! 🛡️\n\n"
                f"🌐 Для подробной информации зайдите в /profile 🔒"
            )

            # Уведомляем дарителя об активации
            if giver:
                await bot.send_message(
                    giver.user_id,
                    f"🎉 Отлично! @{recipient_user.username} активировал ваш подарок! ✨\n"
                    f"💪 Защита {service.name} на {service.duration_days} дней теперь активна!"
                )

            await session_methods.session.commit()

            await logger.log_info(
                f"Пользователь @{receiver_username}, ID {recipient_user_id} активировал подарок от @{giver_username if giver else 'Unknown'}, ID {giver_user_id}: {service_name} на {service_duration} дней"
            )

        except Exception as e:
            await logger.log_error(f'Ошибка при активации подарка {gift_id}', e)
            await callback_query.answer("❌ Произошла ошибка при активации подарка", show_alert=True)


async def run_gift_checker(bot: Bot):
    while True:
        try:
            await gift_checker(bot)
        except Exception as e:
            await logger.log_error("Ошибка в цикле run_checker", e)

        await asyncio.sleep(5)
