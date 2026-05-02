import asyncio
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.context_manager import DatabaseContextManager
from handlers.services.card_service import auto_renewal_payment
from handlers.services.create_receipt import create_receipt
from handlers.services.update_keys import update_keys
from keyboards.kb_inline import SubscriptionCallbackFactory, InlineKeyboards
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import SubscriptionStatusEnum, Payments
from utils.admin_activity_log import admin_activity_message


async def check_subscriptions(bot: Bot):
    subs = []
    async with DatabaseContextManager() as session_methods:
        try:
            subs = await session_methods.subscription.get_subs()
            if len(subs) == 0:
                return
        except Exception as e:
            await logger.log_error(f'Ошибка при получении подписок', e)
            return

    current_date = datetime.utcnow() + timedelta(hours=3)
    for sub in subs:
        async with DatabaseContextManager() as session_methods:
            try:
                await process_subscription(bot, sub, current_date, session_methods)
            except Exception as e:
                await logger.log_error(f'Ошибка обработки подписки {sub.subscription_id}', e)


async def process_subscription(bot: Bot, sub, current_date, session_methods):
    days_since_expiration = (current_date - sub.end_date).days
    days_until_end = (sub.end_date - current_date).days
    if days_until_end == 2 and not sub.reminder_sent:
        await send_reminder(bot, sub, session_methods)

    elif sub.end_date < current_date and sub.status != SubscriptionStatusEnum.EXPIRED:
        await handle_expired_subscription(bot, sub, session_methods)

    elif days_since_expiration > 1 and sub.status == SubscriptionStatusEnum.EXPIRED and sub.reminder_sent != 2:
        await handle_notify_buy_sub(bot, sub, session_methods)


async def send_reminder(bot: Bot, sub, session_methods):
    username = None
    try:
        keyboard = InlineKeyboardBuilder()
        keyboard.add(
            InlineKeyboardButton(
                text='⏳ Продлить подписку',
                callback_data=SubscriptionCallbackFactory(
                    action='extend_subscription',
                    subscription_id=sub.subscription_id
                ).pack(),
            ),
            InlineKeyboardButton(
                text="🎁 Пригласить друга",
                callback_data="referal_subs"
            )
        )

        await session_methods.subscription.update_sub(
            subscription_id=sub.subscription_id,
            reminder_sent=1
        )
        await session_methods.session.commit()
        try:
            await bot.send_message(
                chat_id=sub.user_id,
                text=LEXICON_RU['reminder_sent'],
                reply_markup=keyboard.as_markup(),
                parse_mode="HTML"
            )
            user = await session_methods.users.get_user(sub.user_id)
            username = user.username
            keyboard = await InlineKeyboards.get_user_info(sub.user_id)
        except Exception as e:
            await logger.warning(message=f"Не удалось отправить напоминание: {e}", )
            keyboard = None

        service = None
        if sub.service_id is not None:
            try:
                service = await session_methods.services.get_service_by_id(sub.service_id)
            except Exception:
                pass

        reminder_text = admin_activity_message(
            "Напоминание за ~3 дня до окончания (уведомление пользователю отправлено)",
            user_id=sub.user_id,
            username=username,
            service=service,
            subscription_id=sub.subscription_id,
            payment_response=None,
            extra=(
                f"end_date (UTC в БД): {sub.end_date}\n"
                f"статус: {sub.status}\n"
                f"автопродление: {'да' if sub.auto_renewal else 'нет'}\n"
                f"сохранённая карта (автосписание): {'да' if sub.card_details_id else 'нет'}\n"
                f"service_id в подписке: {sub.service_id}\n"
                f"reminder_sent: выставлен 1 после отправки"
            ),
        )
        try:
            await logger.log_info(reminder_text, keyboard)
        except Exception:
            await logger.log_info(reminder_text)
    except Exception as e:
        await session_methods.session.rollback()
        await logger.log_error(
            f'Пользователь:\nID: {sub.user_id}\nUsername: @{username}\nОшибка при отправке напоминания', e)


async def handle_expired_subscription(bot: Bot, sub, session_methods):
    username = None
    try:
        if sub.auto_renewal and sub.card_details_id:
            service = await session_methods.services.get_service_by_id(sub.service_id)
            res = await auto_renewal_payment(
                amount=service.price,
                description=f"Оплата за услугу: {service.name}",
                payment_method_id=sub.card_details_id,
                user_id=sub.user_id,
                username=username,
                subscription_id=sub.subscription_id,
                service_id=service.service_id
            )
            if res and res['status'] == "succeeded":
                try:
                    receipt_link = await create_receipt(service.name, service.price, service.duration_days)
                except Exception as e:
                    receipt_link = None

                try:
                    await session_methods.payments.create_payments(Payments(
                        payment_id=res['id'],
                        user_id=sub.user_id,
                        service_id=service.service_id,
                        status='succeeded',
                        receipt_link=receipt_link))
                except Exception as e:
                    await logger.warning(message=f"Не удалось создать статус оплаты: {e}")

                try:
                    await session_methods.subscription_history.create_history_entry(
                        user_id=sub.user_id,
                        service_id=service.service_id,
                        start_date=sub.start_date,
                        end_date=sub.end_date,
                        status="автопродление"
                    )
                except Exception as e:
                    await logger.warning(message=f"Не удалось создать историю подписки: {e}")
                try:
                    await bot.send_message(chat_id=sub.user_id, text=f"✅ Ваша подписка успешно продлена!\n"
                                                                     f"Если хотите отключить автопродление, перейдите в свою подписку /profile")
                except:
                    await logger.warning(
                        message=f"Не удалось отправить сообщение о продлении подписки ID: {sub.user_id}")
                new_end_date = sub.end_date + timedelta(days=int(service.duration_days))
                payer = await session_methods.users.get_user(sub.user_id)
                payer_name = payer.username if payer else None
                await logger.log_info(
                    admin_activity_message(
                        "Автопродление: списание успешно",
                        user_id=sub.user_id,
                        username=payer_name,
                        service=service,
                        subscription_id=sub.subscription_id,
                        payment_response=res,
                        extra=(
                            f"новая end_date: {new_end_date}\n"
                            f"payment_method_id (сохранённая карта): {sub.card_details_id}\n"
                            f"запись payments.payment_id: {res.get('id')}"
                        ),
                    )
                )
                await session_methods.subscription.update_sub(
                    subscription_id=sub.subscription_id,
                    status=SubscriptionStatusEnum.ACTIVE,
                    reminder_sent=0,
                    start_date=datetime.now(),
                    end_date=new_end_date
                )
                await session_methods.session.commit()
                return
            else:
                await logger.warning("При автопродление что-то пошло не так")

        await update_keys(user_id=sub.user_id, subscription_id=sub.subscription_id, status=False)

        await session_methods.subscription.update_sub(
            subscription_id=sub.subscription_id,
            status=SubscriptionStatusEnum.EXPIRED,
            reminder_sent=0,
        )
        keyboard = InlineKeyboardBuilder()
        keyboard.add(
            InlineKeyboardButton(
                text='⏳ Продлить подписку',
                callback_data=SubscriptionCallbackFactory(
                    action='extend_subscription',
                    subscription_id=sub.subscription_id
                ).pack(),
            ),
            InlineKeyboardButton(
                text="🎁 Пригласить друга",
                callback_data="referal_subs"
            )
        )
        await session_methods.session.commit()
        user = await session_methods.users.get_user(sub.user_id)
        username = user.username
        try:
            await bot.send_message(
                chat_id=sub.user_id,
                text=LEXICON_RU['expired'],
                reply_markup=keyboard.as_markup(),
            )
            keyboard = await InlineKeyboards.get_user_info(sub.user_id)
        except Exception as e:
            await logger.warning(message=f"Не удалось отправить напоминание @{username}, ID: {sub.user_id}, {e}")
            keyboard = None

        try:
            await logger.log_info(
                f"Подписка у пользователя:\nID: {sub.user_id}\nUsername: @{username}\nИстекла", keyboard
            )
        except:
            await logger.log_info(
                f"Подписка у пользователя:\nID: {sub.user_id}\nUsername: @{username}\nИстекла"
            )
    except Exception as e:
        await session_methods.session.rollback()
        await logger.log_error(
            f'Пользователь:\nID: {sub.user_id}\nUsername: @{username}\nОшибка при обновлении подписки', e)


async def handle_notify_buy_sub(bot, sub, session_methods):
    username = None
    try:
        await session_methods.subscription.update_sub(sub.subscription_id, reminder_sent=2)
        try:
            await bot.send_message(
                chat_id=sub.user_id,
                text=(
                    "Ой! Кажется, ваша подписка закончилась. 😔 Может, пора её продлить? 💪\n\n"
                    "Давайте вернём доступ к вашим любимым функциям! 🚀"
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⏳ Продлить подписку",
                            callback_data=SubscriptionCallbackFactory(
                                action='extend_subscription',
                                subscription_id=sub.subscription_id,
                            ).pack()
                        )
                    ]
                ])
            )
        except:
            pass
        await session_methods.session.commit()
        await logger.info(f"Уведомление о продление подписки отправлено ID: `{sub.user_id}` Username: @{username}")
    except Exception as e:
        await session_methods.session.rollback()
        await logger.error(
            f'Пользователь:\nID: {sub.user_id}\nUsername: @{username}\n'
            f'Ошибка при уведомления пользователя о продление подписки через несколько дней', e)
        await logger.log_error(
            f'Пользователь:\nID: {sub.user_id}\nUsername: @{username}\n'
            f'Ошибка при уведомления пользователя о продление подписки через несколько дней',
            e)


async def run_checker(bot: Bot):
    while True:
        await check_subscriptions(bot)
        await asyncio.sleep(60)
