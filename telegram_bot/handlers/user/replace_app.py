from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.context_manager import DatabaseContextManager
from handlers.services.get_session_cookies import get_session_cookie
from handlers.services.key_create import ShadowsocksKeyManager, VlessKeyManager, ServerUnavailableError
from handlers.user.subs import show_user_subscriptions
from keyboards.kb_inline import InlineKeyboards, SubscriptionCallbackFactory
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import NameApp

router = Router()


@router.callback_query(SubscriptionCallbackFactory.filter(F.action == 'replace_app'))
async def get_support(callback_query: CallbackQuery, state: FSMContext, callback_data: SubscriptionCallbackFactory):
    await callback_query.answer()

    data = await state.get_data()
    previous_message_id = data.get("text_dragons_overview_id")
    if previous_message_id:
        try:
            await callback_query.bot.delete_message(callback_query.message.chat.id, previous_message_id)
            await state.update_data(text_dragons_overview_id=None)
        except Exception as e:
            await logger.log_error(f"Не удалось удалить сообщение с ID {previous_message_id}", e)

    subscription_id = callback_data.subscription_id
    current_app = callback_data.name_app
    new_app = "VLESS" if current_app == "Outline" else "Outline"

    await state.update_data(subscription_id=subscription_id)

    await callback_query.message.edit_text(
        text=LEXICON_RU['choice_app'].format(current_app=current_app, new_app=new_app),
        reply_markup=await InlineKeyboards.replace_app(current_app),
        parse_mode='HTML',
    )


@router.callback_query(SubscriptionCallbackFactory.filter(F.action == "name_app"))
async def handle_server_selection(callback_query: CallbackQuery,
                                  state: FSMContext):
    message = await callback_query.message.edit_text("🔄 Меняем амулет...")

    state_data = await state.get_data()
    subscription_id = int(state_data.get("subscription_id"))

    user_id = callback_query.from_user.id
    username = callback_query.from_user.username

    async with DatabaseContextManager() as session_methods:
        try:
            subscription = await session_methods.subscription.get_subscription_by_id(subscription_id)
            old_key_id = subscription.key_id
            if not subscription:
                raise "Не найдена подписка в базе данных"

            session_cookie = await get_session_cookie(subscription.server_ip)
            if not session_cookie:
                raise ServerUnavailableError(f"Сервер недоступен: {subscription.server_ip}")
            if subscription.name_app == NameApp.OUTLINE:
                name_app = NameApp.VLESS
                vless_manager = VlessKeyManager(subscription.server_ip, session_cookie)
                key, key_id = await vless_manager.manage_vless_key(
                    tg_id=str(user_id),
                    username=username,
                )
                await session_methods.subscription.update_sub(
                    subscription_id=subscription_id,
                    user_id=user_id,
                    key_id=key_id,
                    name_app=name_app,
                    key=key,
                )
                await vless_manager.delete_key(old_key_id)

            elif subscription.name_app == NameApp.VLESS:
                name_app = NameApp.OUTLINE
                shadowsocks_manager = ShadowsocksKeyManager(subscription.server_ip, session_cookie)
                key, key_id = await shadowsocks_manager.manage_shadowsocks_key(
                    tg_id=str(user_id),
                    username=username,
                )
                await session_methods.subscription.update_sub(
                    subscription_id=subscription_id,
                    user_id=user_id,
                    key_id=key_id,
                    name_app=name_app,
                    key=key
                )
                await shadowsocks_manager.delete_key(old_key_id)

            await message.edit_text(
                text=LEXICON_RU["app_changed_success"].format(name_app=name_app, key=key),
                parse_mode="HTML"
            )
            await message.answer(
                text=LEXICON_RU["choose_device"],
                reply_markup=await InlineKeyboards.get_menu_install_app(name_app)
            )
            await session_methods.session.commit()

        except ServerUnavailableError as e:
            await logger.log_error(f'Пользователь: @{callback_query.from_user.username}\nСервер недоступен', e)
            await callback_query.answer(LEXICON_RU["server_unavailable"], show_alert=True)
            await callback_query.message.delete()
            await show_user_subscriptions(
                user_id=callback_query.from_user.id,
                username=callback_query.from_user.username,
                message=callback_query.message,
                state=state)
        except Exception as e:
            await logger.log_error(f'Пользователь: @{callback_query.from_user.username}\n'
                                   f'Ошибка при смене приложения', e)
            await callback_query.message.edit_text(text=LEXICON_RU['error'])
        await state.clear()
