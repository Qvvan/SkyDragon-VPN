from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.context_manager import DatabaseContextManager
from handlers.services.active_servers import get_active_server_and_key
from handlers.services.create_subscription_service import SubscriptionService
from handlers.services.extend_latest_subscription import NoAvailableServersError, extend_user_subscription
from handlers.services.key_create import BaseKeyManager
from keyboards.kb_inline import InlineKeyboards
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import StatusSubscriptionHistory, SubscriptionStatusEnum, Subscriptions, NameApp


class NoActiveSubscriptionsError(Exception):
    pass


class SubscriptionsServiceCard:
    @staticmethod
    async def process_new_subscription(bot: Bot, user_id: int, username: str, service_id: int):
        async with DatabaseContextManager() as session_methods:
            key_id = None
            service = await session_methods.services.get_service_by_id(service_id)
            durations_days = service.duration_days
            try:
                vless_manager, server_ip, key, key_id = await get_active_server_and_key(
                    user_id, username, session_methods
                )

                if not server_ip or not key or not key_id:
                    await logger.log_error(
                        message=f"Пользователь: @{username}, ID {user_id} попытался оформить подписку, но ни один сервер не ответил",
                        error="Не удалось получить сессию ни по одному из серверов"
                    )
                    raise NoAvailableServersError("нет доступных серверов")

                subscription_id = await SubscriptionService.create_subscription(
                    Subscriptions(
                        user_id=user_id,
                        service_id=service_id,
                        key=key,
                        key_id=key_id,
                        server_ip=server_ip,
                        name_app=NameApp.VLESS,
                        start_date=datetime.now(),
                        end_date=datetime.now() + timedelta(days=durations_days)
                    ),
                    session_methods=session_methods
                )
                if not subscription_id:
                    raise Exception("Ошибка создания подписки")

                await session_methods.session.commit()
                await SubscriptionsServiceCard.send_success_response(bot, user_id, key, subscription_id)
                await logger.log_info(f"Пользователь: @{username}\n"
                                      f"ID: {user_id}\n"
                                      f"Оформил подписку на {durations_days} дней")

                try:
                    await SubscriptionsServiceCard.process_referral_bonus(user_id, username, bot)
                except Exception:
                    pass

            except Exception as e:
                if isinstance(e, NoAvailableServersError):
                    await bot.send_message(chat_id=user_id, text=LEXICON_RU['no_servers_available'])
                else:
                    await logger.log_error(f"Пользователь: @{username}, ID {user_id}\nОшибка при обработке транзакции",
                                           e)
                    await bot.send_message(chat_id=user_id, text=LEXICON_RU['purchase_cancelled'])

                await session_methods.session.rollback()

                if vless_manager and key_id:
                    await vless_manager.delete_key(key_id)

                await session_methods.session.commit()

    @staticmethod
    async def extend_sub_successful_payment(bot: Bot, user_id, username, subscription_id, service_id):
        async with DatabaseContextManager() as session_methods:
            try:
                subs = await session_methods.subscription.get_subscription(user_id)
                service = await session_methods.services.get_service_by_id(service_id)
                durations_days = service.duration_days
                if subs:
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
                                user_id=user_id,
                                service_id=sub.service_id,
                                start_date=sub.start_date,
                                end_date=new_end_date,
                                status=StatusSubscriptionHistory.EXTENSION
                            )
                            await BaseKeyManager(server_ip=sub.server_ip).update_key_enable(
                                sub.key_id, True)
                            await logger.info(f"Успешно создана подписка {subscription_id}")
                            await session_methods.session.commit()
                            await bot.send_message(chat_id=user_id, text=LEXICON_RU['subscription_renewed'])
                            await logger.log_info(
                                f"Пользователь: @{username}\n"
                                f"ID: {user_id}\n"
                                f"Продлил подписку на {durations_days} дней"
                            )
                            try:
                                await SubscriptionsServiceCard.process_referral_bonus(
                                    user_id,
                                    username,
                                    bot
                                )
                            except Exception:
                                pass
                            return
                raise NoActiveSubscriptionsError("Нет активных подписок")

            except Exception as e:
                if isinstance(e, NoActiveSubscriptionsError):
                    await bot.send_message(chat_id=user_id,
                                           text="У вас нет активных подписок\n\nОформите новую подписку",
                                           reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                               [
                                                   InlineKeyboardButton(
                                                       text="🐲 Оформить подписку",
                                                       callback_data="subscribe"
                                                   )
                                               ]
                                           ])
                                           )
                else:
                    await bot.send_message(chat_id=user_id, text=LEXICON_RU['purchase_cancelled'])
                await logger.error("Ошибка при продление", e)
                await logger.log_error(
                    f"Пользователь: @{username}\n"
                    f"ID: {user_id}\n"
                    f"Error during transaction processing", e
                )

                await session_methods.session.rollback()
                await session_methods.session.commit()
                return

    @staticmethod
    async def send_success_response(bot: Bot, user_id: int, vpn_key: str, subscription_id):
        await bot.send_message(chat_id=user_id,
                               text=LEXICON_RU[
                                        'purchase_thank_you'] + f'\nКлюч доступа VPN:\n<pre>{vpn_key}</pre>',
                               parse_mode="HTML",
                               )
        await bot.send_message(chat_id=user_id,
                               text=LEXICON_RU["choose_device"],
                               reply_markup=await InlineKeyboards.get_menu_install_app(NameApp.VLESS, subscription_id)
                               )

    @staticmethod
    async def process_referral_bonus(user_id: int, username: str, bot):
        async with DatabaseContextManager() as session_methods:
            try:
                referrer_id = await session_methods.referrals.update_referral_status_if_invited(user_id)
                if referrer_id:
                    await extend_user_subscription(referrer_id, str(username), 15, session_methods)
                    await bot.send_message(referrer_id, LEXICON_RU['referrer_message'].format(username=username))
                    await logger.log_info(
                        f"Пользователь с ID: {referrer_id} получает 15 дня подписки по приглашению: @{username}"
                    )
                    await session_methods.session.commit()
            except Exception as error:
                await session_methods.session.rollback()
                await logger.log_error(
                    f"Ошибка при начислении бонуса за реферал для пользователя с ID: {referrer_id}",
                    error
                )
        return True
