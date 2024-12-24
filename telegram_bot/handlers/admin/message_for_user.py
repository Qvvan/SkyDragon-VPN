from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Создание роутера
router = Router()

# Состояния для FSM
class SendMessageUser(StatesGroup):
    waiting_user_id = State()
    waiting_message = State()
    preview_message = State()

# Буфер для выбранных клавиатур
KEYBOARD_BUFFER = {}

# Предопределённые кнопки для клавиатуры
PREDEFINED_KEYBOARDS = {
    ":show_referrals": "🐲 Приглашенные друзья",
    ":get_invite_link": "🔗 Пригласить друга",
    ":trial_subs": "🐲 Пробный период",
    ":main_menu": "🌌 Главное меню",
    ":view_subs": "🐉 Мои подписки",
    ":faq": "📜 Часто задаваемые вопросы"
}

# Команда для отправки сообщения
@router.message(Command(commands="sms"))
async def start_sending_message(message: types.Message, state: FSMContext):
    await message.answer(
        text="Введите user_id, кому хотите написать:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_send")]]
        )
    )
    await state.set_state(SendMessageUser.waiting_user_id)

# Обработка введённого user_id
@router.message(SendMessageUser.waiting_user_id)
async def process_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(user_id=user_id)
        await message.answer(
            text="Введите текст сообщения:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_send")]]
            )
        )
        await state.set_state(SendMessageUser.waiting_message)
    except ValueError:
        await message.answer("Некорректный user_id. Попробуйте снова.")

# Обработка текста сообщения
@router.message(SendMessageUser.waiting_message)
async def process_message_text(message: types.Message, state: FSMContext):
    text = message.text
    await state.update_data(text=text)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=key)]
        for key, name in PREDEFINED_KEYBOARDS.items()
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="✅ Отправить", callback_data="send_preview")
    ])

    await message.answer(
        text="Выберите кнопки для клавиатуры:",
        reply_markup=keyboard
    )

# Обработка нажатий на кнопки
@router.callback_query()
async def process_keyboard_selection(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data

    if data in PREDEFINED_KEYBOARDS:
        if data not in KEYBOARD_BUFFER:
            KEYBOARD_BUFFER[data] = PREDEFINED_KEYBOARDS[data]
            await callback_query.answer(f"Кнопка '{PREDEFINED_KEYBOARDS[data]}' добавлена.")
        else:
            del KEYBOARD_BUFFER[data]
            await callback_query.answer(f"Кнопка '{PREDEFINED_KEYBOARDS[data]}' удалена.")

        # Обновление клавиатуры
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{PREDEFINED_KEYBOARDS[key]} ✅" if key in KEYBOARD_BUFFER else PREDEFINED_KEYBOARDS[key],
                callback_data=key
            )] for key in PREDEFINED_KEYBOARDS
        ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="✅ Отправить", callback_data="send_preview")
        ])

        await callback_query.message.edit_reply_markup(reply_markup=keyboard)

    elif data == "send_preview":
        user_data = await state.get_data()
        text = user_data.get("text")

        preview_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=key[1:])]
            for key, name in KEYBOARD_BUFFER.items()
        ])
        preview_keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_send"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_send")
        ])

        await callback_query.message.edit_text(
            text=f"Ваше сообщение:\n{text}\n\nПроверьте выбранные кнопки:",
            reply_markup=preview_keyboard
        )
        await state.set_state(SendMessageUser.preview_message)

    elif data == "confirm_send":
        user_data = await state.get_data()
        user_id = user_data.get("user_id")
        text = user_data.get("text")

        real_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=key)]
            for key, name in KEYBOARD_BUFFER.items()
        ])

        try:
            await callback_query.bot.send_message(chat_id=user_id, text=text, reply_markup=real_keyboard)
            await callback_query.message.edit_text("Сообщение успешно отправлено.")
        except Exception as e:
            await callback_query.message.edit_text(f"Ошибка отправки сообщения: {e}")

        await state.clear()

    elif data == "cancel_send":
        await callback_query.message.edit_text("Отправка сообщения отменена.")
        await state.clear()
