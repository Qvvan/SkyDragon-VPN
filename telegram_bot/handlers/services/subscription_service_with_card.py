import asyncio
from datetime import datetime, timedelta

from aiogram import Bot

from database.context_manager import DatabaseContextManager
from handlers.services.create_config_link import create_config_link
from handlers.services.create_subscription_service import SubscriptionService
from handlers.services.extend_latest_subscription import NoAvailableServersError, extend_user_subscription
from handlers.services.key_operations_background import create_keys_background, update_keys_background
from keyboards.kb_inline import InlineKeyboards
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import StatusSubscriptionHistory, SubscriptionStatusEnum, Subscriptions, Gifts
from utils.admin_activity_log import admin_activity_message


class NoActiveSubscriptionsError(Exception):
    pass


class SubscriptionsServiceCard:
    @staticmethod
    async def process_new_subscription(bot: Bot, user_id: int, username: str, service_id: int, payment_response):
        async with DatabaseContextManager() as session_methods:
            service = await session_methods.services.get_service_by_id(service_id)
            durations_days = service.duration_days
            status_saved = payment_response.payment_method.saved
            card_details_id = None
            if status_saved:
                card_details_id = payment_response.payment_method.id
            try:
                subscription = await SubscriptionService.create_subscription(
                    Subscriptions(
                        user_id=user_id,
                        service_id=service_id,
                        start_date=datetime.now(),
                        card_details_id=card_details_id,
                        end_date=datetime.now() + timedelta(days=durations_days)
                    ),
                    session_methods=session_methods
                )
                if not subscription:
                    raise Exception("Ошибка создания подписки")

                config_link = await create_config_link(user_id, subscription.subscription_id)

                # Сразу отправляем успех пользователю
                await SubscriptionsServiceCard.send_success_response(bot, user_id, subscription)
                await session_methods.session.commit()
                await logger.log_info(
                    admin_activity_message(
                        "Покупка: новая подписка (оплата прошла)",
                        user_id=user_id,
                        username=username,
                        service=service,
                        subscription_id=subscription.subscription_id,
                        payment_response=payment_response,
                        extra=(
                            f"end_date (после оплаты): {subscription.end_date}\n"
                            f"дней начислено: {durations_days}"
                        ),
                    )
                )

                # Запускаем создание ключей в фоне (не блокируем ответ пользователю)
                asyncio.create_task(
                    create_keys_background(
                        user_id=user_id,
                        username=username or "",
                        subscription_id=subscription.subscription_id,
                        expiry_days=0,
                    )
                )

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

    @staticmethod
    async def extend_sub_successful_payment(bot: Bot, user_id, username, subscription_id, service_id, payment_response):
        async with DatabaseContextManager() as session_methods:
            try:
                subs = await session_methods.subscription.get_subscription(user_id)
                service = await session_methods.services.get_service_by_id(service_id)
                durations_days = service.duration_days
                status_saved = payment_response.payment_method.saved
                card_details_id = None
                if status_saved:
                    card_details_id = payment_response.payment_method.id
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
                                card_details_id=card_details_id if sub.auto_renewal else None,
                                reminder_sent=0
                            )
                            await session_methods.subscription_history.create_history_entry(
                                user_id=user_id,
                                service_id=sub.service_id,
                                start_date=sub.start_date,
                                end_date=new_end_date,
                                status=StatusSubscriptionHistory.EXTENSION
                            )
                            await logger.info(f"Успешно создана подписка {subscription_id}")
                            await session_methods.session.commit()
                            
                            # Сразу отправляем успех пользователю
                            await bot.send_message(chat_id=user_id, text=LEXICON_RU['subscription_renewed'])
                            await logger.log_info(
                                admin_activity_message(
                                    "Покупка: продление подписки",
                                    user_id=user_id,
                                    username=username,
                                    service=service,
                                    subscription_id=sub.subscription_id,
                                    payment_response=payment_response,
                                    extra=(
                                        f"новая end_date: {new_end_date}\n"
                                        f"дней добавлено: {durations_days}\n"
                                        f"автопродление (карта в подписке обновлена): {bool(sub.auto_renewal and card_details_id)}"
                                    ),
                                )
                            )
                            
                            # Запускаем обновление ключей в фоне (не блокируем ответ пользователю)
                            asyncio.create_task(
                                update_keys_background(
                                    user_id=user_id,
                                    subscription_id=subscription_id,
                                    status=True,
                                )
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

                subscription = await extend_user_subscription(user_id, username, int(durations_days), session_methods)
                
                # Сразу отправляем сообщение пользователю
                await bot.send_message(
                    chat_id=user_id,
                    text="Ваша старая подписка больше не актуальна, поэтому мы создали новую. \n\n"
                         "Чтобы продолжить пользоваться сервисом, нужно заново установить профиль. Это займет всего пару кликов! 🚀"
                )
                await create_config_link(user_id, subscription.subscription_id)
                await SubscriptionsServiceCard.send_success_response(bot, user_id, subscription)
                await session_methods.session.commit()
                await logger.log_info(
                    admin_activity_message(
                        "Продление по оплате → подписка не найдена, создана новая",
                        user_id=user_id,
                        username=username,
                        service=service,
                        subscription_id=getattr(subscription, "subscription_id", None),
                        payment_response=payment_response,
                        extra=(
                            f"запрошенный subscription_id: {subscription_id}\n"
                            f"дней по тарифу: {durations_days}\n"
                            f"новая подписка end_date: {getattr(subscription, 'end_date', None)}"
                        ),
                    )
                )
                
                # Запускаем создание ключей в фоне (не блокируем ответ пользователю)
                asyncio.create_task(
                    create_keys_background(
                        user_id=user_id,
                        username=username or "",
                        subscription_id=subscription.subscription_id,
                        expiry_days=0,
                    )
                )

            except Exception as e:
                await bot.send_message(chat_id=user_id, text=LEXICON_RU['purchase_cancelled'])
                await logger.error("Ошибка при продление", e)
                await logger.log_error(
                    f"Пользователь: @{username}\n"
                    f"ID: {user_id}\n"
                    f"Error during transaction processing", e
                )

                await session_methods.session.rollback()
                return

    @staticmethod
    async def send_success_response(bot: Bot, user_id: int, subscription):
        await bot.send_message(
            chat_id=user_id,
            text=LEXICON_RU["choose_device"],
            reply_markup=await InlineKeyboards.get_menu_install_app(
                subscription.subscription_id,
                user_id=user_id,
            ),
        )

    @staticmethod
    async def process_referral_bonus(user_id: int, username: str, bot):
        async with DatabaseContextManager() as session_methods:
            try:
                referrer_id = await session_methods.referrals.update_referral_status_if_invited(user_id)
                if referrer_id:
                    subscription = await extend_user_subscription(referrer_id, str(username), 15, session_methods)
                    ref_user = await session_methods.users.get_user(referrer_id)
                    ref_username = ref_user.username if ref_user else None
                    await bot.send_message(referrer_id, LEXICON_RU['referrer_message'].format(username=username))
                    await logger.log_info(
                        admin_activity_message(
                            "Реферальный бонус: пригласившему +15 дней",
                            user_id=referrer_id,
                            username=ref_username,
                            service=None,
                            subscription_id=getattr(subscription, "subscription_id", None),
                            payment_response=None,
                            extra=(
                                f"приглашённый user_id: {user_id}\n"
                                f"приглашённый username: @{username or '—'}\n"
                                f"дней бонуса: 15"
                            ),
                        )
                    )
                    await session_methods.session.commit()
                    
                    # Запускаем создание/обновление ключей в фоне
                    if subscription:
                        asyncio.create_task(
                            create_keys_background(
                                user_id=referrer_id,
                                username=str(username) or "",
                                subscription_id=subscription.subscription_id,
                                expiry_days=0,
                            )
                        )
            except Exception as error:
                await session_methods.session.rollback()
                await logger.log_error(
                    f"Ошибка при начислении бонуса за реферал для пользователя с ID: {referrer_id}",
                    error
                )
        return True

    @staticmethod
    async def gift_for_friend(user_id, username, recipient_user_id, service_id, payment_response=None):
        async with DatabaseContextManager() as session_methods:
            try:
                service = await session_methods.services.get_service_by_id(service_id)
                gift_row = await session_methods.gifts.add_gift(Gifts(
                    giver_id=user_id,
                    recipient_user_id=recipient_user_id,
                    service_id=service_id,
                    status="pending",
                ))
                if not gift_row:
                    raise Exception("Не удалось сохранить подарок")
                gift_id = gift_row.gift_id
                await session_methods.session.commit()
                await logger.log_info(
                    admin_activity_message(
                        "Оплата подарка: запись подарка в БД (ожидает вручения получателю)",
                        user_id=user_id,
                        username=username,
                        service=service,
                        subscription_id=None,
                        payment_response=payment_response,
                        extra=(
                            f"gift_id: {gift_id}\n"
                            f"recipient_user_id: {recipient_user_id}\n"
                            f"статус: pending → авто-зачисление при появлении получателя в БД / в фоне"
                        ),
                    )
                )

            except Exception as e:
                await session_methods.session.rollback()
                await logger.log_error(
                    f"Пользователь: @{username}\n"
                    f"ID: {user_id}\n"
                    f"Error during transaction processing with gift", e
                )
