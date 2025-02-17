from datetime import datetime, timedelta

from aiogram import Bot

from database.context_manager import DatabaseContextManager
from handlers.services.create_config_link import create_config_link
from handlers.services.create_keys import create_keys
from handlers.services.create_subscription_service import SubscriptionService
from handlers.services.extend_latest_subscription import NoAvailableServersError, extend_user_subscription
from handlers.services.update_keys import update_keys
from keyboards.kb_inline import InlineKeyboards
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import StatusSubscriptionHistory, SubscriptionStatusEnum, Subscriptions, Gifts


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
                keys = await create_keys(user_id, username)

                subscription = await SubscriptionService.create_subscription(
                    Subscriptions(
                        user_id=user_id,
                        service_id=service_id,
                        key_ids=keys,
                        start_date=datetime.now(),
                        card_details_id=card_details_id,
                        end_date=datetime.now() + timedelta(days=durations_days)
                    ),
                    session_methods=session_methods
                )
                if not subscription:
                    raise Exception("Ошибка создания подписки")

                config_link = await create_config_link(user_id, subscription.subscription_id)

                await session_methods.subscription.update_sub(
                    subscription_id=subscription.subscription_id,
                    config_link=config_link
                )

                await SubscriptionsServiceCard.send_success_response(bot, user_id, config_link, subscription)
                await session_methods.session.commit()
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

                if len(keys) > 0:
                    for key in keys:
                        await logger.warning(f"Данный ключ надо удалить: {key}")

                await session_methods.session.commit()

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
                            await update_keys(subscription_id, True)
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

                subscription = await extend_user_subscription(user_id, username, int(durations_days), session_methods)
                await bot.send_message(
                    chat_id=user_id,
                    text="Ваша старая подписка больше не актуальна, поэтому мы создали новую. \n\n"
                         "Чтобы продолжить пользоваться сервисом, нужно заново установить профиль. Это займет всего пару кликов! 🚀"
                )
                await SubscriptionsServiceCard.send_success_response(bot, user_id, subscription.config_link,
                                                                     subscription)
                await session_methods.session.commit()
                await logger.log_info(
                    f"Пользователь: @{username}\n"
                    f"ID: {user_id}\n"
                    f"Пытался продлить подписку на {durations_days} дней\n"
                    f"Но старой подписки не оказалось, создана новая"
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
    async def send_success_response(bot: Bot, user_id: int, vpn_key: str, subscription):
        await bot.send_message(chat_id=user_id,
                               text=LEXICON_RU[
                                        'purchase_thank_you'] + f'\nКлюч доступа VPN:\n<pre>{vpn_key}</pre>',
                               parse_mode="HTML",
                               )
        await bot.send_message(chat_id=user_id,
                               text=LEXICON_RU["choose_device"],
                               reply_markup=await InlineKeyboards.get_menu_install_app(subscription.subscription_id)
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

    @staticmethod
    async def gift_for_friend(bot, user_id, username, receiver_username, service_id):
        async with DatabaseContextManager() as session_methods:
            try:
                service = await session_methods.services.get_service_by_id(service_id)
                user = await session_methods.users.get_user_by_username(receiver_username)
                if not user:
                    await session_methods.gifts.add_gift(Gifts(
                        giver_id=user_id,
                        receiver_username=receiver_username,
                        service_id=service_id
                    ))
                    await bot.send_message(
                        user_id,
                        "🎁 Возможно, данный пользователь уже зарегистрирован в нашем боте, но его username был обновлён.\n\n"
                        f"Как только @{receiver_username} зайдет в бота, подарок автоматически станет доступным! ✨\n\n"
                        "Спасибо за то, что делитесь радостью! 😊"
                    )
                    await logger.log_info(
                        f"Пользователь: @{receiver_username}\n"
                        f"Получил подарок от пользователя: @{username}\n"
                        f"Подарок: {service.name} на {service.duration_days} дней\n\n"
                        f"❕Но пока пользователь не зарегистрирован в нашем боте❗"
                    )
                else:
                    await session_methods.gifts.add_gift(Gifts(
                        giver_id=user_id,
                        receiver_username=receiver_username,
                        service_id=service_id,
                        status="used",
                        activated_at=datetime.utcnow()
                    ))
                    await extend_user_subscription(user.user_id, receiver_username, service.duration_days,
                                                   session_methods)
                    await bot.send_message(user.user_id,
                                           f"🎁 Вам подарок! 🎉\n\n"
                                           f"Ваш друг {'@' + username if username else 'Неизвестный пользователь'} решил сделать вам приятный сюрприз! ✨\n\n"
                                           f"💪 Защита {service.name}а на {service.duration_days} дней 🛡️\n\n"
                                           f"🌐 Подписка уже активирована, для большей информации зайдите в /profile 🔒"
                                           )
                    await logger.log_info(
                        f"Пользователь: @{receiver_username}\n"
                        f"Получил подарок от пользователя: @{username}\n"
                        f"Подарок: {service.name} на {service.duration_days} дней"
                    )

                await session_methods.session.commit()

            except Exception as e:
                await session_methods.session.rollback()
                await logger.log_error(
                    f"Пользователь: @{username}\n"
                    f"ID: {user_id}\n"
                    f"Error during transaction processing", e
                )
