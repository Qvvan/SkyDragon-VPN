from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.context_manager import DatabaseContextManager
from handlers.services.get_session_cookies import get_session_cookie
from handlers.services.key_create import ShadowsocksKeyManager, VlessKeyManager, ServerUnavailableError
from handlers.user.subs import show_user_subscriptions
from keyboards.kb_inline import InlineKeyboards, ServerSelectCallback, \
    SubscriptionCallbackFactory, ReplaceServerCallbackFactory
from keyboards.kb_reply.kb_inline import ReplyKeyboards
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import NameApp

router = Router()


@router.callback_query(ReplaceServerCallbackFactory.filter(F.action == 'rep_serv'))
async def get_support(callback_query: CallbackQuery, state: FSMContext, callback_data: SubscriptionCallbackFactory):
    """
    Handle replace server callback.

    This function is called when user clicks on a replace server button.
    It answers the callback query, gets the subscription id and server ip
    from the callback data, and updates the state with the subscription id.
    It then gets the list of available servers from the database and
    sends a message to the user with the list of servers and a button
    for each server. If there are no available servers, it sends a message
    with an error message.
    """
    await callback_query.answer()
    subscription_id = callback_data.subscription_id
    server_ip = callback_data.server_ip

    data = await state.get_data()
    previous_message_id = data.get("text_dragons_overview_id")
    if previous_message_id:
        try:
            await callback_query.bot.delete_message(callback_query.message.chat.id, previous_message_id)
            await state.update_data(text_dragons_overview_id=None)
        except Exception as e:
            await logger.log_error(f"Не удалось удалить сообщение с ID {previous_message_id}: {e}")

    await state.update_data(
        subscription_id=subscription_id,
    )
    keyboard = await InlineKeyboards.get_servers(server_ip)
    if not keyboard:
        await callback_query.answer(LEXICON_RU["no_servers_available"], show_alert=True, cache_time=3)
        await show_user_subscriptions(
            user_id=callback_query.from_user.id,
            username=callback_query.from_user.username,
            message=callback_query.message,
            state=state)
    else:
        await callback_query.message.edit_text(
            text=LEXICON_RU["choose_location"],
            reply_markup=keyboard
        )


@router.callback_query(ServerSelectCallback.filter())
async def handle_server_selection(callback_query: CallbackQuery, callback_data: ServerSelectCallback,
                                  state: FSMContext):
    """
    Handle server selection for user.

    This function is called when user selects a new server
    from the list of available servers. It changes the subscription
    server to the selected one, generates a new key for the user,
    and updates the subscription record in the database.

    If the old server is unavailable, it will not be possible
    to delete the old key, and an error will be logged.

    After successful update, it sends a message to the user
    with the new key and asks the user to select his device
    to show the instruction on how to connect to the new server.

    If any error occurs during the process, it sends an error message
    to the user and logs the error.

    Finally, it clears the state.

    :param callback_query: CallbackQuery object that triggered the function
    :param callback_data: ServerSelectCallback object that contains the selected server information
    :param state: FSMContext object that contains the user's state
    """
    message = await callback_query.message.edit_text("🔄 Меняем цитадель...")
    state_data = await state.get_data()
    subscription_id = int(state_data.get("subscription_id"))

    selected_server_ip = callback_data.server_ip
    selected_server_name = callback_data.server_name

    user_id = callback_query.from_user.id
    username = callback_query.from_user.username

    if subscription_id is None:
        await callback_query.message.answer(LEXICON_RU["subscription_not_found_error"])
        return

    async with DatabaseContextManager() as session_methods:
        try:
            # Получаем данные подписки
            subscription = await session_methods.subscription.get_subscription_by_id(subscription_id)
            if not subscription:
                await callback_query.message.answer(LEXICON_RU["subscription_not_found_error"])
                return

            old_key_id = subscription.key_id
            old_server_ip = subscription.server_ip

            # Получаем session_cookie для нового сервера
            session_cookie = await get_session_cookie(selected_server_ip)
            if not session_cookie:
                raise ServerUnavailableError(f"Сервер недоступен: {selected_server_ip}")

            # Генерируем новый ключ в зависимости от типа приложения
            if subscription.name_app == NameApp.OUTLINE:
                shadowsocks_manager = ShadowsocksKeyManager(selected_server_ip, session_cookie)
                key, key_id = await shadowsocks_manager.manage_shadowsocks_key(
                    tg_id=str(user_id),
                    username=username,
                )

                # Удаляем старый ключ, если старый сервер и ключ существуют
                if old_server_ip and old_key_id:
                    try:
                        old_session_cookie = await get_session_cookie(old_server_ip)
                        if old_session_cookie:
                            old_manager = ShadowsocksKeyManager(old_server_ip, old_session_cookie)
                            await old_manager.delete_key(old_key_id)
                    except ServerUnavailableError as e:
                        await logger.log_error(
                            f'Пользователь: @{callback_query.from_user.username}\nСервер недоступен', e)

                # Обновляем данные подписки
                await session_methods.subscription.update_sub(
                    subscription_id=subscription_id,
                    user_id=user_id,
                    key_id=key_id,
                    key=key,
                    server_ip=selected_server_ip
                )

            elif subscription.name_app == NameApp.VLESS:
                vless_manager = VlessKeyManager(selected_server_ip, session_cookie)
                key, key_id = await vless_manager.manage_vless_key(
                    tg_id=str(user_id),
                    username=username,
                )

                # Удаляем старый ключ, если старый сервер и ключ существуют
                if old_server_ip and old_key_id:
                    try:
                        old_session_cookie = await get_session_cookie(old_server_ip)
                        if old_session_cookie:
                            old_manager = VlessKeyManager(old_server_ip, old_session_cookie)
                            await old_manager.delete_key(old_key_id)
                    except ServerUnavailableError as e:
                        await logger.log_error(
                            f'Пользователь: @{callback_query.from_user.username}\nСервер недоступен', e)

                # Обновляем данные подписки
                await session_methods.subscription.update_sub(
                    subscription_id=subscription_id,
                    user_id=user_id,
                    key_id=key_id,
                    key=key,
                    server_ip=selected_server_ip
                )

            # Отправляем сообщение об успешном изменении сервера
            await message.edit_text(
                text=LEXICON_RU["location_changed_success"].format(selected_server_name=selected_server_name, key=key),
                parse_mode="HTML",
            )
            await message.answer(
                text=LEXICON_RU["choose_device"],
                reply_markup=await ReplyKeyboards.get_menu_install_app()
            )
            await session_methods.session.commit()

        except ServerUnavailableError as e:
            await logger.log_error(f'Пользователь: @{callback_query.from_user.username}\nСервер недоступен', e)
            await callback_query.answer(LEXICON_RU["server_unavailable"], show_alert=True)
            await callback_query.message.delete()
        except Exception as e:
            await logger.log_error(f'Пользователь: @{callback_query.from_user.username}\n'
                                   f'Ошибка при смене сервера', e)
            await callback_query.message.edit_text(text=LEXICON_RU['error'])
        await state.clear()
