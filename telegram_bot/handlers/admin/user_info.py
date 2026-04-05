import asyncio

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from filters.admin import IsAdmin
from handlers.services.create_config_link import create_config_link
from handlers.services.extend_latest_subscription import extend_user_subscription
from handlers.services.key_operations_background import create_keys_background
from keyboards.kb_inline import InlineKeyboards, UserInfoCallbackFactory, UserSelectCallback, ChangeUserSubCallback
from logger.logging_config import logger
from models.models import SubscriptionStatusEnum
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
                    f"📲 <b>Happ (iPhone):</b> <code>https://skydragonvpn.ru/import/iphone/happ/{part_link}</code>\n"
                    f"📲 <b>Happ (Android):</b> <code>https://skydragonvpn.ru/import/android/happ/{part_link}</code>\n"
                    f"📲 <b>V2RayTun (iPhone):</b> <code>https://skydragonvpn.ru/import/iphone/v2raytun/{part_link}</code>\n"
                    f"📲 <b>V2RayTun (Android):</b> <code>https://skydragonvpn.ru/import/android/v2raytun/{part_link}</code>\n"
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
