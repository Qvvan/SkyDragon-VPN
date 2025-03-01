from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from filters.admin import IsAdmin
from handlers.services.delete_keys import delete_keys
from handlers.services.extend_latest_subscription import extend_user_subscription
from handlers.services.key_create import BaseKeyManager
from keyboards.kb_inline import InlineKeyboards, UserInfoCallbackFactory, UserSelectCallback, ChangeUserSubCallback
from logger.logging_config import logger
from models.models import SubscriptionStatusEnum
from state.state import KeyInfo, UserSubInfo

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

            # Получаем текущий текст сообщения
            current_text = callback_query.message.text

            # Обновляем статус в тексте
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
                keys_text = await keys_info(sub.key_ids)  # Получаем информацию о ключах

                # Формируем сообщение по подписке
                response_message = (
                    f"🆔 <b>ID подписки:</b> {sub.subscription_id}\n"
                    f"📶 <b>Статус:</b> {'🟢 <b>Активна</b>' if sub.status == SubscriptionStatusEnum.ACTIVE else '🔴 <b>Истекла</b>'}\n"
                    f"🏷 <b>Автопродление:</b> {'✅ Да' if sub.auto_renewal else '❌ Нет'}\n"
                    f"🔑 <b>Конфиг:</b> <code>{sub.config_link}</code>\n"
                    f"📅 <b>Начало:</b> {sub.start_date.strftime('%Y-%m-%d %H:%M')}\n"
                    f"📅 <b>Конец:</b> {sub.end_date.strftime('%Y-%m-%d %H:%M')}\n"
                )

                await callback_query.message.answer(
                    text=response_message,
                    reply_markup=await InlineKeyboards.sub_info(user_id, sub),
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                # Отправляем список ключей (если есть)
                if keys_text:
                    await callback_query.message.answer(text=keys_text, parse_mode="HTML")

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
            await extend_user_subscription(user_id, user.username, duration_days, session_methods)
            await session_methods.session.commit()
            await message.answer("Дата успешно изменена!")

    except ValueError:
        await message.answer('Некорректное количество дней. Попробуйте снова.')

    await state.clear()


@router.callback_query(ChangeUserSubCallback.filter(F.action == "delete_sub"))
async def handle_user_trial(callback_query: CallbackQuery, callback_data: ChangeUserSubCallback):
    async with DatabaseContextManager() as session_methods:
        try:
            await delete_keys(callback_data.subscription_id)
            sub = await session_methods.subscription.get_subscription_by_id(callback_data.subscription_id)

            result = await session_methods.subscription.delete_sub(subscription_id=sub.subscription_id)
            if not result:
                await logger.log_error('Не удалось удалить подписку при ее истечении\n'
                                       f'Пользователь:\nID: {sub.user_id}\n', Exception)
                return

            await session_methods.session.commit()
        except Exception as e:
            await session_methods.session.rollback()
            await logger.log_error(
                f'Пользователь:\nID: {sub.user_id}\nОшибка при удалении подписки', e)

        await callback_query.message.answer("Подписка успешно удалена")


@router.callback_query(ChangeUserSubCallback.filter(F.action == "change_expire_sub"))
async def handle_user_trial(callback_query: CallbackQuery, callback_data: ChangeUserSubCallback):
    await callback_query.message.answer("Вы нажали кнопку изменения автопродления подписки")


@router.callback_query(ChangeUserSubCallback.filter(F.action == "change_status_key"))
async def handle_user_trial(callback_query: CallbackQuery, callback_data: ChangeUserSubCallback):
    async with DatabaseContextManager() as session_methods:
        try:
            sub = await session_methods.subscription.get_subscription_by_id(callback_data.subscription_id)
            key_info = await BaseKeyManager(server_ip=sub.server_ip).get_inbound_by_id(sub.key_id)
            status_key = key_info.get('obj').get('enable')
            await BaseKeyManager(server_ip=sub.server_ip).update_key_enable(sub.key_id, not status_key)
            await callback_query.message.edit_reply_markup()
            await callback_query.answer(
                text=f"Ключ успешно: {'Выключен' if status_key else 'Включен'}",
                show_alert=True,
                cache_time=3
            )
        except Exception as e:
            await logger.error("Произошла ошибка при обновление ключа:", e)
            await callback_query.message.answer("Произошла ошибка при обновление ключа")


async def keys_info(key_ids: list):
    keys_data = []
    total_usage = 0  # Общий трафик

    async with DatabaseContextManager() as session_methods:
        for key_id in key_ids:
            try:
                key = await session_methods.keys.get_key_by_id(key_id)
                if not key:
                    continue

                key_info = await BaseKeyManager(server_ip=key.server_ip).get_inbound_by_id(key.key_id)
                total = key_info.get("obj", {}).get("down", 0)
                total_usage += total

                key_data = {
                    "key_id": key.key_id,
                    "server_ip": key.server_ip,
                    "total": total,
                    "protocol": key_info.get("obj", {}).get("protocol", "Неизвестно"),
                    "enable": "✅ Включен" if key_info.get("obj", {}).get("enable") else "❌ Отключен"
                }

                keys_data.append(key_data)

            except Exception as e:
                await logger.log_error(f"Произошла ошибка при получении ключа {key_id}", e)
                continue

    if not keys_data:
        return ""

    response_text = "<b>🔑 Информация по ключам:</b>\n\n"
    for key in keys_data:
        response_text += (
            f"🆔 <b>ID ключа:</b> {key['key_id']}\n"
            f"🌍 <b>Сервер:</b> {key['server_ip']}\n"
            f"📡 <b>Протокол:</b> {key['protocol']}\n"
            f"📊 <b>Использовано трафика:</b> {human_readable_size(key['total'])}\n"
            f"⚙️ <b>Статус:</b> {key['enable']}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
        )

    response_text += f"\n<b>📊 Общее потребление трафика по всем ключам:</b> {human_readable_size(total_usage)}"
    return response_text


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
