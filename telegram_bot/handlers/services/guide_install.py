from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from database.context_manager import DatabaseContextManager
from handlers.services.create_config_link import create_config_link
from keyboards.kb_inline import InlineKeyboards, SubscriptionCallbackFactory, InstallProfileCallbackFactory
from lexicon.lexicon_ru import guide_install, LEXICON_RU, app_link
from logger.logging_config import logger
from utils.encode_link import encrypt_part

router = Router()


@router.callback_query(SubscriptionCallbackFactory.filter(F.action == 'get_guide_install_app'))
async def back_to_device_selection(
        callback_query: CallbackQuery, state: FSMContext,
        callback_data: SubscriptionCallbackFactory
):
    data = await state.get_data()
    previous_message_id = data.get("text_dragons_overview_id")

    # Функция для безопасного удаления сообщений
    async def delete_message_safe(message_id):
        try:
            await callback_query.bot.delete_message(callback_query.message.chat.id, message_id)
        except Exception as e:
            await logger.info(f"Не удалось удалить сообщение с ID {message_id}")

    if previous_message_id:
        await delete_message_safe(previous_message_id)
        await state.update_data(text_dragons_overview_id=None)

    subscription_id = callback_data.subscription_id
    await callback_query.message.edit_text(
        text=(
            "📘 Откройте ссылку ниже — там пошаговая инструкция и импорт подписки "
            "под ваше устройство.\n\n"
            "Если у вас осталось старое сообщение с выбором Android/iPhone — "
            "те кнопки по-прежнему работают."
        ),
        reply_markup=await InlineKeyboards.get_menu_install_app(
            subscription_id,
            user_id=callback_query.from_user.id,
        )
    )


@router.callback_query(SubscriptionCallbackFactory.filter(F.action.in_({"Android", "iPhone", "Windows", "MacOS"})))
async def get_install_android(callback_query: CallbackQuery, callback_data: SubscriptionCallbackFactory):
    name_device = callback_data.action
    subscription_id = callback_data.subscription_id
    await callback_query.message.edit_text(
        text="Установите приложение, нажав на кнопку 👇",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📲 Установить",
                        url=app_link[name_device]
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👉 Следующий шаг",
                        callback_data=InstallProfileCallbackFactory(
                            action='get_text_install' if name_device in ["Android", "iPhone"] else 'get_manual_install',
                            subscription_id=subscription_id,
                            name_device=name_device
                        ).pack()
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=SubscriptionCallbackFactory(
                            action='get_guide_install_app',
                            subscription_id=subscription_id,
                        ).pack()
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🌌 Главное меню",
                        callback_data="main_menu"
                    )
                ]
            ],

        )
    )


@router.callback_query(InstallProfileCallbackFactory.filter(F.action == 'get_text_install'))
async def get_install_android(callback_query: CallbackQuery, callback_data: InstallProfileCallbackFactory):
    subscription_id = callback_data.subscription_id
    name_device = callback_data.name_device
    async with DatabaseContextManager() as session_methods:
        try:
            sub = await session_methods.subscription.get_subscription_by_id(subscription_id)
            if not sub:
                await callback_query.answer(
                    text=LEXICON_RU["not_found_subscription"],
                    show_alert=True,
                    cache_time=5
                )
                return

            part_link = encrypt_part(str(sub.user_id) + "|" + str(subscription_id))
            url = f"skydragonvpn.ru/import/{name_device.lower()}/{part_link }"
        except Exception as e:
            await logger.log_error(f"При получении подписки что-то пошло не так: {e}")

    await callback_query.message.edit_text(
        text="Выберите способ установки профиля в приложение 👇",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📲 Быстрая",
                        url=url
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🛠 Ручная",
                        callback_data=InstallProfileCallbackFactory(
                            action='get_manual_install',
                            subscription_id=subscription_id,
                            name_device=name_device
                        ).pack()
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data=SubscriptionCallbackFactory(
                            action=name_device,
                            subscription_id=subscription_id,
                        ).pack()
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🌌 Главное меню",
                        callback_data="main_menu"
                    )
                ]
            ]
        )
    )


@router.callback_query(InstallProfileCallbackFactory.filter(F.action == 'get_manual_install'))
async def get_install_android(callback_query: CallbackQuery, callback_data: InstallProfileCallbackFactory,
                              state: FSMContext):
    name_device = callback_data.name_device
    subscription_id = callback_data.subscription_id
    async with DatabaseContextManager() as session_methods:
        try:
            subscription = await session_methods.subscription.get_subscription_by_id(subscription_id)
            if not subscription:
                await callback_query.answer(LEXICON_RU["not_found_subscription"], show_alert=True, cache_time=5)
                return

            await callback_query.answer()
            config_link = await create_config_link(user_id=subscription.user_id, sub_id=subscription.subscription_id)
            show_guide_message = await callback_query.message.edit_text(
                text=guide_install[name_device].format(key=config_link),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔙 Назад",
                                callback_data=InstallProfileCallbackFactory(
                                    action='get_text_install',
                                    subscription_id=subscription_id,
                                    name_device=name_device
                                ).pack() if name_device in ["Android", "iPhone"] else SubscriptionCallbackFactory(
                                    action=name_device,
                                    subscription_id=subscription_id
                                ).pack()
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="🌌 Главное меню",
                                callback_data="main_menu"
                            )
                        ]
                    ]
                ),
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            await state.update_data(show_guide_message=show_guide_message.message_id)
        except Exception as e:
            await logger.log_error(f"Не удалось получить подписку при показе инструкции {callback_query.from_user.id}",
                                   e)
