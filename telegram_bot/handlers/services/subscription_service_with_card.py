from datetime import datetime, timedelta

from aiogram import Bot

from database.context_manager import DatabaseContextManager
from handlers.services.create_config_link import create_config_link
from handlers.services.extend_latest_subscription import NoAvailableServersError, extend_user_subscription
from handlers.services.key_operations_background import enqueue_create, enqueue_enable
from keyboards.kb_inline import InlineKeyboards
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import StatusSubscriptionHistory, SubscriptionStatusEnum, Gifts


class NoActiveSubscriptionsError(Exception):
    pass


class SubscriptionsServiceCard:
    @staticmethod
    async def process_new_subscription(bot: Bot, user_id: int, username: str, service_id: int, payment_response):
        """
        Обрабатывает успешную оплату новой подписки.
        Если у пользователя уже есть подписка — продлевает самую позднюю.
        Если нет — создаёт новую.
        """
        async with DatabaseContextManager() as session_methods:
            try:
                service = await session_methods.services.get_service_by_id(service_id)
                duration_days = service.duration_days
                status_saved = payment_response.payment_method.saved
                card_details_id = payment_response.payment_method.id if status_saved else None

                subscription, is_new = await extend_user_subscription(
                    user_id=user_id,
                    username=username,
                    days=duration_days,
                    session_methods=session_methods,
                    service_id=service_id,
                )
                if not subscription:
                    raise Exception("Ошибка создания/продления подписки")

                # Сохраняем card_details_id если нужно
                if card_details_id and subscription.auto_renewal:
                    await session_methods.subscription.update_sub(
                        subscription_id=subscription.subscription_id,
                        card_details_id=card_details_id,
                    )

                # Ставим операцию с ключами в ту же транзакцию
                if is_new:
                    await enqueue_create(user_id, subscription.subscription_id, session_methods)
                else:
                    await enqueue_enable(user_id, subscription.subscription_id, session_methods)

                await session_methods.session.commit()

                await SubscriptionsServiceCard.send_success_response(bot, user_id, subscription)
                await logger.log_info(
                    f"Пользователь: @{username}\n"
                    f"ID: {user_id}\n"
                    f"{'Оформил' if is_new else 'Продлил'} подписку на {duration_days} дней"
                )

                try:
                    await SubscriptionsServiceCard.process_referral_bonus(user_id, username, bot)
                except Exception:
                    pass

            except Exception as e:
                if isinstance(e, NoAvailableServersError):
                    await bot.send_message(chat_id=user_id, text=LEXICON_RU['no_servers_available'])
                else:
                    await logger.log_error(
                        f"Пользователь: @{username}, ID {user_id}\nОшибка при обработке транзакции", e
                    )
                    await bot.send_message(chat_id=user_id, text=LEXICON_RU['purchase_cancelled'])
                await session_methods.session.rollback()

    @staticmethod
    async def extend_sub_successful_payment(
        bot: Bot, user_id: int, username: str, subscription_id: int, service_id: int, payment_response
    ):
        """
        Обрабатывает успешную оплату продления конкретной подписки.
        Находит подписку по subscription_id и продлевает её end_date.
        """
        async with DatabaseContextManager() as session_methods:
            try:
                service = await session_methods.services.get_service_by_id(service_id)
                duration_days = service.duration_days
                status_saved = payment_response.payment_method.saved
                card_details_id = payment_response.payment_method.id if status_saved else None

                subs = await session_methods.subscription.get_subscription(user_id)
                target = next((s for s in subs if s.subscription_id == subscription_id), None) if subs else None

                if target:
                    # Продлеваем найденную подписку
                    if datetime.now() > target.end_date:
                        new_end_date = datetime.now() + timedelta(days=int(duration_days))
                    else:
                        new_end_date = target.end_date + timedelta(days=int(duration_days))

                    await session_methods.subscription.update_sub(
                        subscription_id=target.subscription_id,
                        service_id=service_id,
                        end_date=new_end_date,
                        updated_at=datetime.now(),
                        status=SubscriptionStatusEnum.ACTIVE,
                        card_details_id=card_details_id if target.auto_renewal else None,
                        reminder_sent=0,
                    )
                    await session_methods.subscription_history.create_history_entry(
                        user_id=user_id,
                        service_id=target.service_id,
                        start_date=target.start_date,
                        end_date=new_end_date,
                        status=StatusSubscriptionHistory.EXTENSION,
                    )
                    await enqueue_enable(user_id, target.subscription_id, session_methods)
                    await session_methods.session.commit()

                    await bot.send_message(chat_id=user_id, text=LEXICON_RU['subscription_renewed'])
                    await logger.log_info(
                        f"Пользователь: @{username}\n"
                        f"ID: {user_id}\n"
                        f"Продлил подписку на {duration_days} дней"
                    )
                else:
                    # Целевой подписки не нашли — создаём/продлеваем последнюю
                    subscription, is_new = await extend_user_subscription(
                        user_id, username, int(duration_days), session_methods
                    )
                    await enqueue_create(user_id, subscription.subscription_id, session_methods)
                    await session_methods.session.commit()

                    await bot.send_message(
                        chat_id=user_id,
                        text="Ваша старая подписка больше не актуальна, поэтому мы создали новую.\n\n"
                             "Чтобы продолжить пользоваться сервисом, нужно заново установить профиль. "
                             "Это займет всего пару кликов! 🚀"
                    )
                    await create_config_link(user_id, subscription.subscription_id)
                    await SubscriptionsServiceCard.send_success_response(bot, user_id, subscription)
                    await logger.log_info(
                        f"Пользователь: @{username}\n"
                        f"ID: {user_id}\n"
                        f"Создана новая подписка вместо устаревшей ({duration_days} дней)"
                    )

                try:
                    await SubscriptionsServiceCard.process_referral_bonus(user_id, username, bot)
                except Exception:
                    pass

            except Exception as e:
                await bot.send_message(chat_id=user_id, text=LEXICON_RU['purchase_cancelled'])
                await logger.log_error(
                    f"Пользователь: @{username}\nID: {user_id}\nОшибка при продлении", e
                )
                await session_methods.session.rollback()

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
                    subscription, is_new = await extend_user_subscription(
                        referrer_id, str(username), 15, session_methods
                    )
                    if is_new:
                        await enqueue_create(referrer_id, subscription.subscription_id, session_methods)
                    else:
                        await enqueue_enable(referrer_id, subscription.subscription_id, session_methods)
                    await session_methods.session.commit()

                    await bot.send_message(referrer_id, LEXICON_RU['referrer_message'].format(username=username))
                    await logger.log_info(
                        f"Пользователь с ID: {referrer_id} получает 15 дней подписки по приглашению: @{username}"
                    )
            except Exception as error:
                await session_methods.session.rollback()
                await logger.log_error(
                    f"Ошибка при начислении бонуса за реферал для пользователя с ID: {user_id}", error
                )
        return True

    @staticmethod
    async def gift_for_friend(user_id, username, recipient_user_id, service_id):
        async with DatabaseContextManager() as session_methods:
            try:
                await session_methods.gifts.add_gift(Gifts(
                    giver_id=user_id,
                    recipient_user_id=recipient_user_id,
                    service_id=service_id,
                    status="pending",
                ))
                await session_methods.session.commit()
            except Exception as e:
                await session_methods.session.rollback()
                await logger.log_error(
                    f"Пользователь: @{username}\nID: {user_id}\nОшибка при создании подарка", e
                )
