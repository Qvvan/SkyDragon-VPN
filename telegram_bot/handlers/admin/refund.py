from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from keyboards.kb_inline import InlineKeyboards
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from state.state import CancelTransaction

router = Router()


@router.message(Command(commands="refund"))
async def start_another_feature(message: types.Message, state: FSMContext):
    await message.answer(
        text="Введите код транзакции",
        reply_markup=await InlineKeyboards.cancel()
    )
    await state.set_state(CancelTransaction.waiting_for_transaction)


@router.message(CancelTransaction.waiting_for_transaction)
async def process_another_input(message: types.Message, state: FSMContext):
    transaction_code = message.text
    await state.update_data(transaction_code=transaction_code)
    await state.set_state(CancelTransaction.waiting_for_user)
    await message.answer("Введите ID пользователя:")


@router.message(CancelTransaction.waiting_for_user)
async def process_another_input(message: types.Message, state: FSMContext):
    user_id = int(message.text)
    data = await state.get_data()
    transaction_code = data.get('transaction_code')
    result = await cancel_transaction(user_id, transaction_code, message.bot)
    if result['success']:
        await message.answer("Транзакция успешно отменена!")
    else:
        await message.answer(result['message'])

    await state.clear()


async def cancel_transaction(user_id: int, transaction_code: str, bot) -> dict:
    try:
        if user_id and transaction_code:
            try:
                await bot.refund_star_payment(user_id, transaction_code)
                await bot.send_message(chat_id=user_id, text=LEXICON_RU['refund_message'])
                return {'success': True, 'message': 'Транзакция успешно отменена!'}
            except:
                return {'success': False, 'message': 'Транзакция уже отменена'}
        else:
            return {'success': False, 'message': 'Нет такой транзакции'}

    except Exception as e:
        await logger.log_error('Не удалось отменить транзакцию', e)
        return {'success': False, 'message': f"Не удалось отменить транзакцию, ошибка:\n{str(e)}"}
