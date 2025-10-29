import base64
import hashlib
import uuid

from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from filters.admin import IsAdmin
from handlers.services.key_create import BaseKeyManager
from keyboards.kb_inline import InlineKeyboards
from logger.logging_config import logger

router = Router()


class KeyCreationStates(StatesGroup):
    waiting_for_ip = State()


@router.message(Command(commands='new_keys'), IsAdmin(ADMIN_IDS))
async def show_commands(message: types.Message, state: FSMContext):
    await state.set_state(KeyCreationStates.waiting_for_ip)
    await message.answer(
        text='Отправьте IP сервера',
        reply_markup=await InlineKeyboards.cancel()
    )


@router.message(KeyCreationStates.waiting_for_ip, F.text)
async def process_ip_address(message: types.Message, state: FSMContext):
    server_ip = message.text.strip()

    # Простая валидация IP-адреса
    if not is_valid_ip(server_ip):
        await message.answer(
            text='❌ Неверный формат IP-адреса. Попробуйте еще раз:',
            reply_markup=await InlineKeyboards.cancel()
        )
        return

    await message.answer('⏳ Начинаю создание ключей...')

    # Запускаем создание ключей
    result = await create_keys(server_ip)

    if result:
        await message.answer('✅ Ключи успешно созданы!')
    else:
        await message.answer('❌ Произошла ошибка при создании ключей. Проверьте логи.')

    # Очищаем состояние
    await state.clear()


@router.callback_query(F.data == 'cancel', KeyCreationStates.waiting_for_ip)
async def cancel_key_creation(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text('❌ Создание ключей отменено.')
    await callback.answer()


def is_valid_ip(ip: str) -> bool:
    """Проверяет корректность IP-адреса"""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except (ValueError, AttributeError):
        return False


async def create_keys(server_ip: str):
    async with DatabaseContextManager() as session_methods:
        try:
            subs = await session_methods.subscription.get_subs()
            for sub in subs:
                sub_uuid = encode_numbers(sub.user_id, sub.subscription_id)
                client_id = generate_deterministic_uuid(sub.user_id, sub.subscription_id)
                try:
                    base = BaseKeyManager(server_ip)
                    client_uuid, email, url_config = await base.add_client_to_inbound(
                        tg_id=str(sub.user_id),
                        sub_id=sub_uuid,
                        client_id=client_id
                    )
                    if client_uuid is None:
                        continue

                except Exception as e:
                    await logger.log_error(f"Ошибка создания ключа на сервер {server_ip}", e)
            return True

        except Exception as e:
            await logger.log_error("Ошибка при поиске активного сервера или создании ключа", e)
            return False


def encode_numbers(user_id: int, sub_id: int, secret_key: str = "my_secret_key") -> str:
    data = f"{user_id},{sub_id}"

    checksum = hashlib.sha256((data + secret_key).encode()).hexdigest()[:8]

    combined = f"{data}|{checksum}"

    encoded = base64.b64encode(combined.encode()).decode()

    return encoded


def generate_deterministic_uuid(user_id: int, sub_id: int) -> str:
    """
    Генерирует детерминированный UUID из user_id и sub_id
    Всегда возвращает одинаковый UUID для одинаковых входных данных
    """
    # Создаем уникальную строку из user_id и sub_id
    unique_string = f"user_{user_id}_sub_{sub_id}"

    # Используем namespace UUID (можешь создать свой)
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace

    # Генерируем UUID v5 (детерминированный)
    deterministic_uuid = uuid.uuid5(namespace, unique_string)

    return str(deterministic_uuid)
