import asyncio

from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.context_manager import DatabaseContextManager
from keyboards.kb_inline import UserPaginationCallback, InlineKeyboards, UserSelectCallback
from logger.logging_config import logger

router = Router()


@router.message(Command(commands="pushes"))
async def start_broadcast(message: types.Message, state: FSMContext):
    """Начало показа пользователей с кнопками навигации."""
    async with DatabaseContextManager() as session_methods:
        try:
            users = await session_methods.users.get_all_users()
            users_dict = {user.user_id: {'user_id': user.user_id, 'username': user.username, 'selected': False} for user
                          in
                          users}
            await state.update_data(users=users_dict)
        except Exception as e:
            await logger.error('Произошла ошибка при старте pushes', e)
    page = 1
    await show_users(message, page, users_dict)


@router.callback_query(UserSelectCallback.filter())
async def select_user(callback_query: types.CallbackQuery, callback_data: UserSelectCallback, state: FSMContext):
    try:
        data = await state.get_data()
        users_dict = data.get('users', {})
        user_id = callback_data.user_id
        if user_id in users_dict:
            users_dict[user_id]['selected'] = not users_dict[user_id]['selected']
            await state.update_data(users=users_dict)
        page = (list(users_dict.keys()).index(user_id) // 5) + 1
        await show_users(callback_query.message, page, users_dict)
        await callback_query.answer()
        await state.update_data(current_page=page)
    except Exception as e:
        await logger.error('Произошла ошибка при обработке выбора пользователя', e)


@router.callback_query(lambda call: call.data in ['add_all_users', 'add_active_users', 'cancel_all'])
async def handle_special_buttons(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    data = await state.get_data()
    users_dict = data.get('users', {})
    if callback_query.data == 'add_all_users':
        for user in users_dict.values():
            user['selected'] = True
    elif callback_query.data == 'add_active_users':
        async with DatabaseContextManager() as session_methods:
            active_user_ids = await session_methods.subscription.get_active_subscribed_users()
        for user_id, user in users_dict.items():
            user['selected'] = user_id in active_user_ids
    elif callback_query.data == 'cancel_all':
        for user in users_dict.values():
            user['selected'] = False
    await state.update_data(users=users_dict)
    page = 1
    await show_users(callback_query.message, page, users_dict)
    await callback_query.answer()


@router.callback_query(lambda call: call.data == 'save')
async def handle_save_button(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    users_dict = data.get('users', {})
    selected_users = [user for user in users_dict.values() if user['selected']]
    if not selected_users:
        await callback_query.answer("Не выбрано ни одного пользователя", show_alert=True)
        return
    await state.update_data(selected_users=selected_users)
    await callback_query.message.edit_text("Напишите текст для уведомления")
    await state.set_state("waiting_for_message_text")


@router.message(StateFilter("waiting_for_message_text"))
async def handle_message_text(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите текст для уведомления.")
        return

    await state.update_data(message_text=message.text)
    data = await state.get_data()
    selected_users = data.get('selected_users', [])

    await message.answer(
        f"Текст уведомления сохранен\n\n{message.text}\n\nКоличество получателей: {len(selected_users)}.",
        reply_markup=await InlineKeyboards.show_notify_change_cancel()
    )
    await state.set_state(None)


@router.callback_query(lambda call: call.data == 'edit_message')
async def edit_message(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Напишите новый текст для уведомления")
    await state.set_state("waiting_for_message_text")


@router.callback_query(lambda call: call.data == 'send_notification')
async def send_notification(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_text = data.get('message_text')
    selected_users = data.get('selected_users', [])

    if not message_text:
        await callback_query.answer("Текст уведомления отсутствует. Пожалуйста, задайте текст перед отправкой.",
                                    show_alert=True)
        return
    await callback_query.answer("Начинаю рассылку...", show_alert=False, cache_time=3)

    count = 0
    blocked_users = []
    successful_user_ids = []
    batch_size = 20  # Размер батча для отправки сообщений
    delay_between_batches = 2  # Задержка между батчами (в секундах)

    async def send_message(user):
        nonlocal count
        async with DatabaseContextManager() as session_methods:
            try:
                user_info = await session_methods.users.get_user(user['user_id'])
                if user_info.ban:
                    return
                try:
                    await callback_query.bot.send_message(
                        chat_id=user['user_id'],
                        text=message_text,
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="🐲 Мои подписки",
                                    callback_data="view_subs"
                                )
                            ],
                        ])
                    )
                    successful_user_ids.append(user['user_id'])
                    count += 1
                except Exception as e:
                    blocked_users.append(user['user_id'])
                    await session_methods.users.update_user(user['user_id'], ban=True)
                    await session_methods.session.commit()
            except Exception as e:
                await logger.log_error(f"Ошибка при отправке пользователю {user['user_id']}", e)

    # Разделяем пользователей на батчи и отправляем сообщения
    for i in range(0, len(selected_users), batch_size):
        batch = selected_users[i:i + batch_size]
        await asyncio.gather(*(send_message(user) for user in batch))
        await callback_query.message.answer(f"Отправлено {count} уведомлений.")
        await asyncio.sleep(delay_between_batches)

    # Обновление базы данных для заблокировавших пользователей
    async with DatabaseContextManager() as session_methods:
        try:
            await logger.info(f"Обновлено состояние бана для пользователей: {blocked_users}")
            await session_methods.pushes.add_push_record(message=message_text, user_ids=successful_user_ids)
            await session_methods.session.commit()
        except Exception as e:
            await logger.log_error("Не удалось обновить базу данных", e)

    # Отправляем итоговое сообщение
    await callback_query.message.edit_text(
        f"Готово 🎉\n"
        f"Уведомление отправлено {count} пользователям.\n"
        f"Заблокировали бота: {len(blocked_users)}"
    )


@router.callback_query(UserPaginationCallback.filter())
async def paginate_users(callback_query: types.CallbackQuery, callback_data: UserPaginationCallback, state: FSMContext):
    data = await state.get_data()
    users_dict = data.get('users', {})
    page = callback_data.page
    if callback_data.action == 'next' and (page * 5) < len(users_dict):
        page += 1
        await show_users(callback_query.message, page, users_dict)
        return
    elif callback_data.action == 'previous' and page > 1:
        page -= 1
        await show_users(callback_query.message, page, users_dict)
        return
    await callback_query.answer()
    """Обработка нажатий на кнопки пагинации."""
    data = await state.get_data()
    users_dict = data.get('users', {})
    page = callback_data.page
    if callback_data.action == 'next' and page * 5 < len(users_dict) or callback_data.action == 'previous' and page > 1:
        await show_users(callback_query.message, page, users_dict)
    await callback_query.answer()


async def show_users(message: types.Message, page: int, users_dict: dict):
    users = list(users_dict.values())[5 * (page - 1):5 * page]
    has_next = len(users_dict) > page * 5
    try:
        keyboard = await InlineKeyboards.create_user_pagination_with_users_keyboard(users, page, has_next)
        user_list = "Кому отправим уведомления?"
        if not user_list:
            user_list = "No users found."
    except Exception as e:
        await logger.error('Произошла ошибка при создании клавиатуры', e)
        return

    # Отправляем сообщение с пользователями и клавиатурой
    try:
        await message.edit_text(user_list, reply_markup=keyboard)
    except:
        await message.answer(user_list, reply_markup=keyboard)
