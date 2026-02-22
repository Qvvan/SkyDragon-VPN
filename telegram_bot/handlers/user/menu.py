from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.kb_inline import InlineKeyboards, MAIN_MENU_BTN, MAIN_MENU_CB
from lexicon.lexicon_ru import LEXICON_RU

router = Router()


@router.message(Command(commands="main_menu"))
async def process_start_command(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(back_target='main_menu')
    await message.answer(
        text=LEXICON_RU['main_menu'],
        reply_markup=await InlineKeyboards.main_menu(message.from_user.id),
        parse_mode="Markdown"
    )


@router.callback_query(lambda c: c.data == 'main_menu')
async def handle_know_more(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(back_target='main_menu')
    await callback.message.edit_text(
        text=LEXICON_RU['main_menu'],
        reply_markup=await InlineKeyboards.main_menu(callback.from_user.id),
        parse_mode="Markdown"
    )


@router.callback_query(lambda c: c.data == 'my_gifts')
async def handle_my_gifts(callback: CallbackQuery):
    """Обработчик кнопки 'Мои подарки'"""
    await callback.answer()

    from database.context_manager import DatabaseContextManager

    async with DatabaseContextManager() as session_methods:
        try:
            # Получаем пользователя
            user = await session_methods.users.get_user(callback.from_user.id)
            if not user:
                await callback.message.edit_text(
                    "❌ Не удалось найти ваш профиль",
                    reply_markup=InlineKeyboards.row_main_menu()
                )
                return

            # Получаем подарки пользователя
            gifts = await session_methods.gifts.get_gifts(callback.from_user.id)
            user_gifts = [gift for gift in gifts if gift.status == "awaiting_activation"]

            if not user_gifts:
                await callback.message.edit_text(
                    "🎁 У вас нет подарков для активации",
                    reply_markup=InlineKeyboards.row_main_menu()
                )
                return

            # Формируем сообщение с подарками
            message_text = f"🎁 **Ваши подарки:**\n\n"

            keyboard = []
            for i, gift in enumerate(user_gifts, 1):
                try:
                    service = await session_methods.services.get_service_by_id(gift.service_id)
                    giver = await session_methods.users.get_user(gift.giver_id)

                    service_name = service.name if service else "Неизвестная услуга"
                    service_days = service.duration_days if service else "?"
                    giver_name = f"@{giver.username}" if giver and giver.username else "Неизвестный пользователь"

                    message_text += f"{i}. **{service_name}** на {service_days} дней\n"
                    message_text += f"   От: {giver_name}\n\n"

                    # Добавляем кнопку активации для каждого подарка
                    keyboard.append([
                        InlineKeyboardButton(
                            text=f"🎁 Активировать подарок {i}",
                            callback_data=f"activate_gift_{gift.gift_id}"
                        )
                    ])
                except Exception:
                    continue

            keyboard.append([InlineKeyboardButton(text=MAIN_MENU_BTN, callback_data=MAIN_MENU_CB)])

            await callback.message.edit_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode="Markdown"
            )

        except Exception as e:
            await callback.message.edit_text(
                "❌ Произошла ошибка при загрузке подарков",
                reply_markup=InlineKeyboards.row_main_menu()
            )
