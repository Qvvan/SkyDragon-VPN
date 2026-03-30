import asyncio
from datetime import datetime, timedelta

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from filters.admin import IsAdmin
from handlers.services.create_config_link import create_config_link
from handlers.services.create_subscription_service import SubscriptionService
from handlers.services.delete_keys import delete_keys
from handlers.services.extend_latest_subscription import extend_user_subscription
from handlers.services.key_operations_background import create_keys_background
from keyboards.kb_inline import InlineKeyboards, UserInfoCallbackFactory, UserSelectCallback, ChangeUserSubCallback
from logger.logging_config import logger
from models.models import SubscriptionStatusEnum, Subscriptions
from state.state import KeyInfo, UserSubInfo
from utils.encode_link import encrypt_part

router = Router()


@router.message(Command(commands='user_info'), IsAdmin(ADMIN_IDS))
async def show_commands(message: types.Message, state: FSMContext):
    await message.answer(
        text='Отправьте ID пользователя',
        reply_markup=await InlineKeyboards.cancel()
    )
    await state.set_state(KeyInfo.waiting_key_info)


@router.message(KeyInfo.waiting_key_info)
async def user_info(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = int(message.text)
    async with DatabaseContextManager() as session_methods:
        try:
            user_info = await session_methods.users.get_user(user_id)
            response_user = (
                f"👤 Пользователь: @{user_info.username}\n"
                f"🆔 ID пользователя: {user_info.user_id}\n"
                f"🚫 Статус Бана: {'🟢 Не забанен' if user_info.ban == 0 else '🔴 Забанен'}\n"
                f"🎁 Пробная подписка: {'🟢 Использована' if user_info.trial_used else '🔴 Не использована'}\n"
                f"⏱️ Последний визит: {user_info.last_visit.strftime('%d.%m.%Y %H:%M')}\n"
                f"📅 Дата регистрации: {user_info.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            )

            await message.answer(
                text=response_user,
                reply_markup=await InlineKeyboards.user_info(
                    user_id=user_id,
                    ban=user_info.ban,
                    trial=user_info.trial_used),
            )
            await state.clear()

        except Exception as e:
            await message.answer(f"Произошла ошибка: \n{e}")


@router.callback_query(UserInfoCallbackFactory.filter(F.action == "user_ban"))
async def handle_user_ban(callback_query: CallbackQuery, callback_data: UserInfoCallbackFactory):
    user_id = callback_data.user_id
    ban_status = callback_data.ban

    async with DatabaseContextManager() as session_methods:
        try:
            await session_methods.users.update_user(user_id=user_id, ban=ban_status)
            await session_methods.session.commit()

            # Получаем текущий текст сообщения
            current_text = callback_query.message.text
            # Обновляем статус в тексте
            updated_text = current_text.replace(
                "🟢 Не забанен" if ban_status else "🔴 Забанен",
                "🔴 Забанен" if ban_status else "🟢 Не забанен"
            )

            # Создаём обновлённую клавиатуру
            updated_keyboard = await InlineKeyboards.user_info(
                user_id=user_id,
                ban=ban_status,
                trial=callback_data.trial
            )

            # Проверяем, изменилось ли сообщение
            if updated_text != current_text or callback_query.message.reply_markup != updated_keyboard:
                await callback_query.message.edit_text(text=updated_text, reply_markup=updated_keyboard)

            await callback_query.answer(f"Пользователь {'забанен' if ban_status else 'разбанен'}.")

        except Exception as e:
            await callback_query.answer(f"Ошибка: {e}", show_alert=True)


@router.callback_query(UserInfoCallbackFactory.filter(F.action == "user_trial"))
async def handle_user_trial(callback_query: CallbackQuery, callback_data: UserInfoCallbackFactory):
    user_id = callback_data.user_id
    trial_status = callback_data.trial

    async with DatabaseContextManager() as session_methods:
        try:
            await session_methods.users.update_user(user_id=user_id, trial_used=trial_status)
            await session_methods.session.commit()

            current_text = callback_query.message.text

            updated_text = current_text.replace(
                "🟢 Использована" if not trial_status else "🔴 Не использована",
                "🔴 Не использована" if not trial_status else "🟢 Использована"
            )

            # Обновляем клавиатуру
            updated_keyboard = await InlineKeyboards.user_info(
                user_id=user_id,
                ban=callback_data.ban,
                trial=trial_status
            )

            # Применяем изменения текста и клавиатуры
            await callback_query.message.edit_text(text=updated_text, reply_markup=updated_keyboard)

            await callback_query.answer(f"Пробная подписка {'включена' if trial_status else 'выключена'}.")
            await logger.info(
                f"Пробная подписка пользователя {user_id} {'включена' if trial_status else 'выключена'} администратором.")

        except Exception as e:
            await callback_query.answer(f"Ошибка: {e}", show_alert=True)
            await logger.log_error(f"Ошибка при изменении статуса пробной подписки пользователя {user_id}", e)


@router.callback_query(UserSelectCallback.filter(F.action == "user_subs_info"))
async def handle_user_subscriptions(callback_query: CallbackQuery, callback_data: UserSelectCallback):
    user_id = int(callback_data.user_id)

    async with DatabaseContextManager() as session_methods:
        try:
            subs = await session_methods.subscription.get_subscription(user_id)
            if not subs:
                await callback_query.answer(
                    text="У данного пользователя нет доступных подписок",
                    show_alert=True,
                    cache_time=5
                )
                return

            await callback_query.answer()

            for sub in subs:
                config_link = await create_config_link(user_id=user_id, sub_id=sub.subscription_id)
                part_link = encrypt_part(str(user_id) + "|" + str(sub.subscription_id))
                response_message = (
                    f"🆔 <b>ID подписки:</b> {sub.subscription_id}\n"
                    f"📶 <b>Статус:</b> {'🟢 <b>Активна</b>' if sub.status == SubscriptionStatusEnum.ACTIVE else '🔴 <b>Истекла</b>'}\n"
                    f"🏷 <b>Автопродление:</b> {'✅ Да' if sub.auto_renewal else '❌ Нет'}\n"
                    f"🔑 <b>Конфиг:</b> <code>{config_link}</code>\n"
                    f"📲 <b>Для айфона:</b> <code>https://skydragonvpn.ru/import/iphone/{part_link}</code>\n"
                    f"📲 <b>Для андроида:</b> <code>https://skydragonvpn.ru/import/android/{part_link}</code>\n"
                    f"📅 <b>Начало:</b> {sub.start_date.strftime('%Y-%m-%d %H:%M')}\n"
                    f"📅 <b>Конец:</b> {sub.end_date.strftime('%Y-%m-%d %H:%M')}\n"
                )

                await callback_query.message.answer(
                    text=response_message,
                    reply_markup=await InlineKeyboards.sub_info(user_id, sub),
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )

        except Exception as e:
            await logger.error(f"Произошла ошибка:", e)
            await callback_query.message.answer(f"⚠️ <b>Произошла ошибка:</b>\n<code>{e}</code>", parse_mode="HTML")


@router.callback_query(ChangeUserSubCallback.filter(F.action == "change_date_sub"))
async def handle_user_trial(callback_query: CallbackQuery, callback_data: ChangeUserSubCallback, state: FSMContext):
    await state.update_data(user_id=int(callback_data.user_id))
    await callback_query.message.answer(
        text='Введите количество дней:',
        reply_markup=await InlineKeyboards.cancel()
    )
    await state.set_state(UserSubInfo.waiting_duration_days)


@router.message(UserSubInfo.waiting_duration_days)
async def process_duration_days(message: types.Message, state: FSMContext):
    try:
        duration_days = int(message.text)
        data = await state.get_data()
        user_id = data.get('user_id')

        async with DatabaseContextManager() as session_methods:
            user = await session_methods.users.get_user(user_id)
            subscription = await extend_user_subscription(
                user_id, user.username or "", duration_days, session_methods
            )
            await session_methods.session.commit()
            await message.answer("Дата успешно изменена!")

            if subscription:
                asyncio.create_task(
                    create_keys_background(
                        user_id=user_id,
                        username=user.username or "",
                        subscription_id=subscription.subscription_id,
                        expiry_days=0,
                    )
                )

    except ValueError:
        await message.answer('Некорректное количество дней. Попробуйте снова.')

    await state.clear()


@router.callback_query(ChangeUserSubCallback.filter(F.action == "change_expire_sub"))
async def handle_user_trial(callback_query: CallbackQuery, callback_data: ChangeUserSubCallback):
    await callback_query.message.answer("Вы нажали кнопку изменения автопродления подписки")

@router.callback_query(ChangeUserSubCallback.filter(F.action == "delete_sub"))
async def handle_delete_subscription(
    callback_query: CallbackQuery,
    callback_data: ChangeUserSubCallback,
):
    user_id = int(callback_data.user_id)
    subscription_id = int(callback_data.subscription_id)

    await callback_query.answer()

    async with DatabaseContextManager() as session_methods:
        try:
            sub = await session_methods.subscription.get_subscription_by_id(subscription_id)
            if not sub or int(sub.get("user_id") or -1) != user_id:
                await callback_query.answer("Подписка не найдена.", show_alert=True)
                return

            # 1) Удаляем ключи на серверах
            await delete_keys(user_id=user_id, subscription_id=subscription_id)

            # 2) Удаляем запись о подписке в БД
            deleted = await session_methods.subscription.delete_sub(subscription_id)
            if deleted:
                await session_methods.session.commit()
                await callback_query.message.edit_text(
                    f"✅ Подписка {subscription_id} удалена.\nКлючи удалены на серверах.",
                    reply_markup=await InlineKeyboards.cancel(),
                )
            else:
                await session_methods.session.rollback()
                await callback_query.message.edit_text(
                    f"⚠️ Не удалось удалить подписку {subscription_id} из БД.",
                    reply_markup=await InlineKeyboards.cancel(),
                )
        except Exception as e:
            await session_methods.session.rollback()
            await logger.log_error(
                f"Ошибка удаления подписки: user_id={user_id}, subscription_id={subscription_id}",
                e,
            )
            await callback_query.message.edit_text(
                f"⚠️ Ошибка при удалении подписки: <code>{e}</code>",
                parse_mode="HTML",
            )


@router.callback_query(ChangeUserSubCallback.filter(F.action == "reissue_sub"))
async def handle_reissue_subscription(
    callback_query: CallbackQuery,
    callback_data: ChangeUserSubCallback,
):
    user_id = int(callback_data.user_id)
    old_subscription_id = int(callback_data.subscription_id)

    await callback_query.answer()

    async with DatabaseContextManager() as session_methods:
        try:
            old_sub = await session_methods.subscription.get_subscription_by_id(old_subscription_id)
            if not old_sub or int(old_sub.get("user_id") or -1) != user_id:
                await callback_query.answer("Подписка не найдена.", show_alert=True)
                return

            duration_days = int(old_sub.get("duration_days") or 0)
            service_id = int(old_sub.get("service_id") or 0)
            if duration_days <= 0 or service_id <= 0:
                await callback_query.answer(
                    "Не удалось определить длительность/сервис для перевыпуска.",
                    show_alert=True,
                )
                return

            username = ""
            try:
                user = await session_methods.users.get_user(user_id)
                username = user.username or ""
            except Exception:
                username = ""

            # 1) Удаляем ключи со старой подписки на серверах
            await delete_keys(user_id=user_id, subscription_id=old_subscription_id)

            # 2) Удаляем старую подписку в БД
            deleted = await session_methods.subscription.delete_sub(old_subscription_id)
            if not deleted:
                await session_methods.session.rollback()
                await callback_query.message.edit_text(
                    "⚠️ Не удалось удалить старую подписку в БД.",
                    reply_markup=await InlineKeyboards.cancel(),
                )
                return

            # 3) Создаём новую подписку (новый subscription_id) в БД
            start_date = datetime.now()
            end_date = start_date + timedelta(days=duration_days)
            auto_renewal = bool(old_sub.get("auto_renewal", True))
            card_details_id = old_sub.get("card_details_id") if auto_renewal else None

            new_sub = Subscriptions(
                user_id=user_id,
                service_id=service_id,
                start_date=start_date,
                end_date=end_date,
                status=SubscriptionStatusEnum.ACTIVE,
                reminder_sent=0,
                auto_renewal=auto_renewal,
                card_details_id=card_details_id,
            )

            created = await SubscriptionService.create_subscription(new_sub, session_methods)
            if not created:
                await session_methods.session.rollback()
                await callback_query.message.edit_text(
                    "⚠️ Ошибка: не удалось создать новую подписку в БД.",
                    reply_markup=await InlineKeyboards.cancel(),
                )
                return

            await session_methods.session.commit()

            new_subscription_id = created.subscription_id
            config_link = await create_config_link(user_id=user_id, sub_id=new_subscription_id)

            # 4) Создаём новые ключи (в фоне)
            asyncio.create_task(
                create_keys_background(
                    user_id=user_id,
                    username=username,
                    subscription_id=new_subscription_id,
                    expiry_days=0,
                )
            )

            await callback_query.message.edit_text(
                "✅ Подписка перевыпущена.\n"
                f"Было: {old_subscription_id}\n"
                f"Стало: {new_subscription_id}\n"
                f"Конфиг: <code>{config_link}</code>\n"
                "Ключи создаются на серверах.",
                parse_mode="HTML",
                reply_markup=await InlineKeyboards.cancel(),
            )
        except Exception as e:
            await session_methods.session.rollback()
            await logger.log_error(
                f"Ошибка перевыпуска подписки: user_id={user_id}, old_subscription_id={old_subscription_id}",
                e,
            )
            await callback_query.message.edit_text(
                f"⚠️ Ошибка при перевыпуске подписки: <code>{e}</code>",
                parse_mode="HTML",
            )


def human_readable_size(size: int) -> str:
    """Конвертирует байты в читаемый формат (KB, MB, GB, TB)"""
    if size == 0:
        return "0 B"
    sizes = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size >= 1024 and i < len(sizes) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {sizes[i]}"
