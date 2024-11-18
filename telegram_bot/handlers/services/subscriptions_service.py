from datetime import datetime, timedelta

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.context_manager import DatabaseContextManager
from handlers.services.active_servers import get_active_server_and_key
from handlers.services.create_subscription_service import SubscriptionService
from handlers.services.create_transaction_service import TransactionService
from handlers.services.extend_latest_subscription import NoAvailableServersError, extend_user_subscription
from handlers.services.get_session_cookies import get_session_cookie
from handlers.services.key_create import BaseKeyManager
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import StatusSubscriptionHistory, SubscriptionStatusEnum, Subscriptions, NameApp


class SubscriptionsService:
    """
    Сервис для обработки подписок в системе.

    Этот класс управляет процессом создания и продления подписок, а также обработкой транзакций.
    """

    @staticmethod
    async def process_new_subscription(message: Message):
        """
        Обрабатывает новую подписку при успешном платеже.

        Принимает сообщение с информацией о платеже, создает транзакцию и подписку,
        а затем отправляет пользователю уведомление с ключом доступа.

        Args:
            message (telegram.Message): Сообщение от Telegram, содержащее информацию о платеже.

        Raises:
            Exception: Если не удалось сохранить транзакцию или создать подписку.
        """
        async with DatabaseContextManager() as session_methods:
            shadowsocks_manager = None
            key_id = None

            try:
                in_payload = message.successful_payment.invoice_payload.split(':')
                duration_date = in_payload[1]
                user_id = message.from_user.id
                username = message.from_user.username

                transaction_state = await TransactionService.create_transaction(
                        message, 'successful', 'successful', session_methods
                        )
                if not transaction_state:
                    raise Exception("Ошибка сохранения транзакции")

                # Получение активного сервера и создание Shadowsocks ключа
                shadowsocks_manager, server_ip, key, key_id = await get_active_server_and_key(
                        user_id, username, session_methods
                        )

                if not server_ip or not key or not key_id:
                    await logger.log_error(
                            message=f"Пользователь: @{username} попытался оформить подписку, но ни один сервер не ответил",
                            error="Не удалось получить сессию ни по одному из серверов"
                            )
                    raise NoAvailableServersError("нет доступных серверов")

                # Создание подписки
                service_id = int(in_payload[0])
                durations_days = int(in_payload[1])
                subscription_created = await SubscriptionService.create_subscription(
                    Subscriptions(
                        user_id=user_id,
                        service_id=service_id,
                        key=key,
                        key_id=key_id,
                        server_ip=server_ip,
                        name_app=NameApp.OUTLINE,
                        start_date=datetime.now(),
                        end_date=datetime.now() + timedelta(days=durations_days)
                    ),
                    session_methods=session_methods
                )
                if not subscription_created:
                    raise Exception("Ошибка создания подписки")

                # Коммит сессии после успешных операций
                await session_methods.session.commit()
                await SubscriptionsService.send_success_response(message, key)
                await logger.log_info(f"Пользователь: @{username} оформил подписку на {duration_date} дней")

                # Изолированное начисление бонуса
                try:
                    await SubscriptionsService.process_referral_bonus(user_id, username, message.bot)
                except Exception:
                    pass

            except Exception as e:
                if isinstance(e, NoAvailableServersError):
                    await message.answer(text=LEXICON_RU['no_servers_available'])
                else:
                    await logger.log_error(f"Пользователь: @{username}\nОшибка при обработке транзакции", e)
                    await message.answer(text=LEXICON_RU['purchase_cancelled'])

                await SubscriptionsService.refund_payment(message)

                # Откат транзакции
                await session_methods.session.rollback()

                # Удаление ключа при наличии shadowsocks_manager и key_id
                if shadowsocks_manager and key_id:
                    await shadowsocks_manager.delete_key(key_id)

                # Сохранение транзакции с отменой
                await TransactionService.create_transaction(
                        message, status='отмена', description=str(e), session_methods=session_methods
                        )
                await session_methods.session.commit()

    @staticmethod
    async def extend_sub_successful_payment(message: Message, state: FSMContext):
        """
        Обрабатывает успешное продление подписки для пользователя.

        Args:
            message (Message): Сообщение от Telegram, содержащее информацию о платеже.
            state (FSMContext): Состояние для подписки, которую будем продлять.
        """
        async with DatabaseContextManager() as session_methods:
            try:
                in_payload = message.successful_payment.invoice_payload.split(':')
                service_id = int(in_payload[0])
                durations_days = int(in_payload[1])
                user_data = await state.get_data()
                subscription_id = user_data.get('subscription_id')

                # Получение текущей подписки пользователя
                subs = await session_methods.subscription.get_subscription(message.from_user.id)
                if subs:
                    transaction_state = await TransactionService.create_transaction(
                            message, 'successful', 'successful', session_methods
                            )
                    if not transaction_state:
                        raise Exception("Ошибка сохранения транзакции")

                    for sub in subs:
                        if sub.subscription_id == subscription_id:
                            if datetime.now() > sub.end_date:
                                new_end_date = datetime.now() + timedelta(days=int(durations_days))
                            else:
                                new_end_date = sub.end_date + timedelta(days=int(durations_days))
                            await session_methods.subscription.update_sub(
                                    subscription_id=sub.subscription_id,
                                    service_id=service_id,
                                    end_date=new_end_date,
                                    updated_at=datetime.now(),
                                    status=SubscriptionStatusEnum.ACTIVE,
                                    reminder_sent=0
                                    )
                            await session_methods.subscription_history.create_history_entry(
                                    user_id=message.from_user.id,
                                    service_id=sub.service_id,
                                    start_date=sub.start_date,
                                    end_date=new_end_date,
                                    status=StatusSubscriptionHistory.EXTENSION
                                    )
                            session = await get_session_cookie(sub.server_ip)
                            await BaseKeyManager(server_ip=sub.server_ip, session_cookie=session).update_key_enable(
                                sub.key_id, True)
                            await session_methods.session.commit()
                            await message.answer(text=LEXICON_RU['subscription_renewed'])
                            await logger.log_info(
                                f"Пользователь: @{message.from_user.username}\n"
                                f"Продлил подписку на {durations_days} дней"
                                )
                else:
                    await message.answer(text="Подписка не найдена. Проверьте данные.")

            except Exception as e:
                await logger.log_error(
                    f"Пользователь: @{message.from_user.username}\n"
                    f"Error during transaction processing", e
                    )
                await message.answer(text=LEXICON_RU['purchase_cancelled'])

                await SubscriptionsService.refund_payment(message)

                await session_methods.session.rollback()

                await TransactionService.create_transaction(
                        message, status='отмена', description=str(e), session_methods=session_methods
                        )
                await session_methods.session.commit()

    @staticmethod
    async def send_success_response(message: Message, vpn_key: str):
        """
        Отправляет пользователю успешное уведомление с VPN ключом.

        Args:
            message (telegram.Message): Сообщение от Telegram, в которое будет отправлено уведомление.
            vpn_key (str): Ключ доступа VPN, который будет отправлен пользователю.
        """
        await message.answer(
                text=LEXICON_RU[
                         'purchase_thank_you'] + f'\nИмя твоего дракона 🐉 теперь звучит как:\n<pre>{vpn_key}</pre>',
                parse_mode="HTML",
                )
        await message.answer(
                text=LEXICON_RU['choose_device'],
                )

    @staticmethod
    async def refund_payment(message: Message):
        """
        Обрабатывает возврат платежа через Telegram.

        Args:
            message (telegram.Message): Сообщение от Telegram, содержащее информацию о платеже.
        """
        await message.bot.refund_star_payment(
            message.from_user.id,
            message.successful_payment.telegram_payment_charge_id
            )

    @staticmethod
    async def process_referral_bonus(user_id: int, username: str, bot):
        async with DatabaseContextManager() as session_methods:
            try:
                referrer_id = await session_methods.referrals.update_referral_status_if_invited(user_id)
                if referrer_id:
                    await extend_user_subscription(referrer_id, 23, session_methods)
                    await bot.send_message(referrer_id, LEXICON_RU['referrer_message'].format(username=username))
                    await logger.log_info(
                            f"Пользователь с ID: {referrer_id} получает 23 дня подписки по приглашению: @{username}"
                            )
                    await session_methods.session.commit()
            except Exception as error:
                await session_methods.session.rollback()
                await logger.log_error(
                    f"Ошибка при начислении бонуса за реферал для пользователя с ID: {referrer_id}",
                    error
                    )
        return True
