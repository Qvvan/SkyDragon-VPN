from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from filters.admin import IsAdmin
from handlers.services.identifiers import encode_numbers, generate_deterministic_uuid
from handlers.services.panel_gateway import PanelGateway
from keyboards.kb_inline import InlineKeyboards, ServerCallbackData
from logger.logging_config import logger
from models.models import Servers

router = Router()


class KeyCreationStates(StatesGroup):
    waiting_for_server = State()


@router.message(Command(commands='new_keys'), IsAdmin(ADMIN_IDS))
async def show_servers_for_keys(message: types.Message, state: FSMContext):
    await state.set_state(KeyCreationStates.waiting_for_server)
    async with DatabaseContextManager() as session_methods:
        servers = await session_methods.servers.get_all_servers()
    # Показываем только не скрытые серверы
    servers = [s for s in servers if getattr(s, 'hidden', 0) != 1]
    if not servers:
        await state.clear()
        await message.answer('❌ Нет доступных серверов.')
        return
    buttons = [
        [InlineKeyboardButton(
            text=f"{s.name or s.server_ip} ({s.server_ip})",
            callback_data=ServerCallbackData(action='new_keys', server_ip=s.server_ip).pack()
        )]
        for s in servers
    ]
    buttons.append([InlineKeyboardButton(text='❌ Отмена', callback_data='cancel')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        text='Выберите сервер для создания ключей:',
        reply_markup=keyboard
    )


@router.callback_query(
    ServerCallbackData.filter(F.action == 'new_keys'),
    KeyCreationStates.waiting_for_server
)
async def process_server_selected(
    callback: types.CallbackQuery,
    callback_data: ServerCallbackData,
    state: FSMContext
):
    server_ip = callback_data.server_ip
    await callback.answer()
    await callback.message.edit_text(f'⏳ Создаю ключи на сервере {server_ip}...')

    ok, success_count, total_attempts = await create_keys(server_ip)

    if not ok:
        await callback.message.edit_text(
            '❌ Произошла ошибка при создании ключей. Проверьте логи.'
        )
    elif total_attempts == 0:
        await callback.message.edit_text(
            f'ℹ️ Нет активных подписок для создания ключей на сервере {server_ip}.'
        )
    elif success_count == total_attempts:
        await callback.message.edit_text(
            f'✅ Ключи успешно созданы на {server_ip}! ({success_count} ключей)'
        )
    else:
        await callback.message.edit_text(
            f'⚠️ На {server_ip} создано {success_count} из {total_attempts} ключей. '
            'Проверьте логи при необходимости.'
        )
    await state.clear()


@router.callback_query(F.data == 'cancel', KeyCreationStates.waiting_for_server)
async def cancel_key_creation(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text('❌ Создание ключей отменено.')
    await callback.answer()


async def create_keys(server_ip: str) -> tuple[bool, int, int]:
    """
    Создает ключи для всех активных подписок на указанном сервере.
    Использует новый PanelGateway с поддержкой множественных портов.

    Returns:
        (ok, success_count, total_attempts):
        - ok: False только при реальной ошибке (сервер не найден, исключение)
        - success_count: сколько ключей создано
        - total_attempts: сколько попыток (подписки × порты)
    """
    async with DatabaseContextManager() as session_methods:
        try:
            # Получаем сервер из БД
            server = await session_methods.servers.get_server_by_ip(server_ip)
            if not server:
                await logger.error(f"Сервер {server_ip} не найден в базе данных", None)
                return (False, 0, 0)

            # Определяем список портов для этого сервера
            available_ports = server.available_ports or [443]

            subs = await session_methods.subscription.get_active_subscribed()
            success_count = 0
            total_attempts = 0

            if not subs:
                await logger.info(
                    f"Админ: на сервере {server_ip} нет активных подписок для создания ключей"
                )

            for sub in subs:
                sub_uuid = encode_numbers(sub.user_id, sub.subscription_id)
                client_id = generate_deterministic_uuid(sub.user_id, sub.subscription_id)

                # Создаем ключи на всех портах из available_ports
                for port in available_ports:
                    total_attempts += 1
                    try:
                        gateway = PanelGateway(server)
                        
                        # Формируем уникальный email для каждого порта
                        email = f"{sub_uuid}_port{port}"
                        
                        result = await gateway.add_client(
                            port=port,
                            client_id=client_id,
                            email=email,
                            tg_id=str(sub.user_id),
                            sub_id=sub_uuid,
                            limit_ip=1,
                            expiry_days=0,  # Без ограничений для админского создания
                            enable=True,
                        )

                        if result:
                            success_count += 1
                            await logger.info(
                                f"Админ: ключ создан для user_id={sub.user_id}, sub_id={sub.subscription_id}, "
                                f"server={server_ip}, port={port}"
                            )
                        else:
                            await logger.warning(
                                f"Админ: не удалось создать ключ для user_id={sub.user_id}, "
                                f"sub_id={sub.subscription_id}, server={server_ip}, port={port}"
                            )

                        await gateway.close()

                    except Exception as e:
                        await logger.log_error(
                            f"Админ: ошибка создания ключа на сервер {server_ip}, порт {port}, "
                            f"user_id={sub.user_id}, sub_id={sub.subscription_id}", e
                        )

            await logger.info(
                f"Админ: создание ключей завершено для сервера {server_ip}, "
                f"успешно={success_count}/{total_attempts}"
            )
            return (True, success_count, total_attempts)

        except Exception as e:
            await logger.log_error("Ошибка при поиске активного сервера или создании ключа", e)
            return (False, 0, 0)


