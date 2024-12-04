from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from filters.admin import IsAdmin
from keyboards.kb_inline import InlineKeyboards, UserInfoCallbackFactory, UserSelectCallback
from logger.logging_config import logger
from models.models import SubscriptionStatusEnum
from state.state import KeyInfo

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
                f"👤 *Пользователь:* @{user_info.username}\n"
                f"🆔 *ID пользователя:* {user_info.user_id}\n"
                f"🚫 *Статус Бана:* {'🟢 Не забанен' if user_info.ban == 0 else '🔴 Забанен'}\n"
                f"🎁 *Пробная подписка:* {'🟢 Использована' if user_info.trial_used else '🔴 Не использована'}\n"
                f"⏱️ *Последний визит:* {user_info.last_visit.strftime('%d.%m.%Y %H:%M')}\n"
                f"📅 *Дата регистрации:* {user_info.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            )

            await message.answer(
                text=response_user,
                reply_markup=await InlineKeyboards.user_info(
                    user_id=user_id,
                    ban=user_info.ban,
                    trial=user_info.trial_used),
                parse_mode="Markdown"
            )

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
            await logger.info(f"Пробная подписка пользователя {user_id} {'включена' if trial_status else 'выключена'} администратором.")

        except Exception as e:
            await callback_query.answer(f"Ошибка: {e}", show_alert=True)
            await logger.log_error(f"Ошибка при изменении статуса пробной подписки пользователя {user_id}", e)


@router.callback_query(UserSelectCallback.filter(F.action == "user_subs"))
async def handle_user_trial(callback_query: CallbackQuery, callback_data: UserSelectCallback):
    user_id = int(callback_data.user_id)
    async with DatabaseContextManager() as session_methods:
        try:
            subs = await session_methods.subscription.get_subscription(user_id)
            if len(subs) == 0:
                await callback_query.answer(
                    text='У данного пользователя нет доступных подписок',
                    show_alert=True,
                    cache_time=5
                )
            for sub in subs:
                response_message = (
                    f"🆔 ID подписки: {sub.subscription_id}\n"
                    f"📶 Статус: {'🟢 Активна' if sub.status == SubscriptionStatusEnum.ACTIVE else '🔴 Истекла'}\n"
                    f"🌐 Сервер: {sub.server_ip}\n"
                    f"🏷 Имя сервера: {sub.server_name}\n"
                    f"🔑 Ключ: {sub.key}\n"
                    f"🆔 ID Ключа: {sub.key_id}\n"
                    f"📅 Начало подписки: {sub.start_date.strftime('%Y-%m-%d %H:%M')}\n"
                    f"📅 Конец подписки: {sub.end_date.strftime('%Y-%m-%d %H:%M')}\n\n"
                )
                message_sub_info = await callback_query.message.answer(
                    text=response_message,
                    reply_markup=await InlineKeyboards.sub_info(sub.subscription_id),
                )
        except Exception as e:
            await callback_query.message.answer(f"Произошла ошибка: \n{e}")


@router.callback_query(UserSelectCallback.filter(F.action == "turn_off_sub"))
async def handle_user_trial(callback_query: CallbackQuery, callback_data: UserSelectCallback):
    await callback_query.message.answer('Вы нажали кнопку выключить подписку')


@router.callback_query(UserSelectCallback.filter(F.action == "end_date_sub"))
async def handle_user_trial(callback_query: CallbackQuery, callback_data: UserSelectCallback):
    await callback_query.message.answer('Вы нажали кнопку настройки даты подписки')