import asyncio
from datetime import datetime, timedelta

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config_data.config import ADMIN_IDS
from database.context_manager import DatabaseContextManager
from filters.admin import IsAdmin
from handlers.services.extend_latest_subscription import extend_user_subscription
from handlers.services.key_operations_background import create_keys_background, update_keys_background
from keyboards.kb_inline import InlineKeyboards
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import Users, Subscriptions
from state.state import GiveSub

router = Router()


@router.message(Command(commands=['add_gift', 'grant_sub']), IsAdmin(ADMIN_IDS))
async def show_commands(message: types.Message, state: FSMContext):
    await message.answer(
        text='Введите Telegram ID пользователя, которому хотите выдать подписку:',
        reply_markup=await InlineKeyboards.cancel()
    )
    await state.set_state(GiveSub.waiting_username)


@router.message(GiveSub.waiting_username)
async def process_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        if user_id <= 0:
            raise ValueError

        await state.update_data(user_id=user_id)
        await message.answer(
            text='Введите количество дней подписки:',
            reply_markup=await InlineKeyboards.cancel()
        )
        await state.set_state(GiveSub.waiting_duration_days)
    except ValueError:
        await message.answer('Некорректный Telegram ID. Введите положительное число.')


@router.message(GiveSub.waiting_duration_days)
async def process_duration_days(message: types.Message, state: FSMContext):
    try:
        duration_days = int(message.text)
        if duration_days <= 0:
            raise ValueError

        await state.update_data(duration_days=duration_days)
        await message.answer(
            "Как выдать подписку?\n\n"
            "Введите:\n"
            "продлить — продлить/обновить текущую\n"
            "новая — создать новую отдельную подписку",
            reply_markup=await InlineKeyboards.cancel()
        )
        await state.set_state(GiveSub.waiting_issue_mode)
        return
    except ValueError:
        await message.answer('Некорректное количество дней. Введите положительное число.')


@router.message(GiveSub.waiting_issue_mode)
async def process_issue_mode(message: types.Message, state: FSMContext):
    raw_mode = (message.text or "").strip().lower()
    issue_mode_map = {
        "продлить": "extend",
        "продление": "extend",
        "extend": "extend",
        "новая": "new",
        "новую": "new",
        "new": "new",
    }
    issue_mode = issue_mode_map.get(raw_mode)
    if issue_mode is None:
        await message.answer(
            "Некорректный выбор. Введите: продлить или новая.",
            reply_markup=await InlineKeyboards.cancel()
        )
        return

    await state.update_data(issue_mode=issue_mode)
    await message.answer(
        "Отправить уведомление пользователю?\n\n"
        "Введите: да / нет",
        reply_markup=await InlineKeyboards.cancel()
    )
    await state.set_state(GiveSub.waiting_notification_preference)


@router.message(GiveSub.waiting_notification_preference)
async def process_notification_preference(message: types.Message, state: FSMContext):
    raw_preference = (message.text or "").strip().lower()
    notify_user_map = {
        "да": True,
        "д": True,
        "yes": True,
        "y": True,
        "нет": False,
        "н": False,
        "no": False,
        "n": False,
    }

    notify_user = notify_user_map.get(raw_preference)
    if notify_user is None:
        await message.answer(
            "Некорректный выбор. Введите только: да или нет.",
            reply_markup=await InlineKeyboards.cancel()
        )
        return

    try:
        data = await state.get_data()
        user_id = data.get('user_id')
        duration_days = data.get('duration_days')
        issue_mode = data.get('issue_mode', 'extend')
        if not user_id or not duration_days:
            await message.answer("Не удалось получить данные выдачи. Повторите команду.")
            await state.clear()
            return

        async with DatabaseContextManager() as session_methods:
            user = await session_methods.users.get_user(user_id)
            user_was_created = False
            had_subscriptions_before_issue = False
            if not user:
                user = Users(user_id=user_id, username=None)
                if await session_methods.users.add_user(user):
                    user_was_created = True
            else:
                existing_subs = await session_methods.subscription.get_subscription(user_id)
                had_subscriptions_before_issue = bool(existing_subs)

            if issue_mode == "new":
                subscription = await session_methods.subscription.create_sub(
                    Subscriptions(
                        user_id=user_id,
                        service_id=0,
                        start_date=datetime.now(),
                        end_date=datetime.now() + timedelta(days=duration_days),
                    )
                )
                if not subscription:
                    raise Exception("Ошибка создания новой подписки")
            else:
                subscription = await extend_user_subscription(
                    user_id, user.username, duration_days, session_methods
                )

            await session_methods.subscription_history.create_history_entry(
                user_id=user_id,
                service_id=subscription.service_id,
                start_date=subscription.start_date,
                end_date=subscription.end_date,
                status="gift"
            )
            await session_methods.session.commit()

            if notify_user:
                try:
                    await message.bot.send_message(
                        chat_id=user_id,
                        text=LEXICON_RU['add_gift_success'].format(duration_days=duration_days),
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [
                                    InlineKeyboardButton(
                                        text="🐉 Мои подписки",
                                        callback_data="view_subs"
                                    )
                                ],
                            ]
                        )
                    )
                except Exception:
                    await logger.warning(
                        f"Не удалось отправить уведомление пользователю с ID: {user_id}. "
                        "Вероятно, пользователь еще не запускал бота."
                    )
            else:
                await logger.info(f"Подписка пользователю ID: {user_id} выдана без уведомления.")

            await logger.log_info(
                f"Администрация выдала подписку пользователю ID: {user_id}\n"
                f"Дней: {duration_days}\n"
                f"Режим выдачи: {'новая подписка' if issue_mode == 'new' else 'продление'}\n"
                f"Уведомление: {'да' if notify_user else 'нет'}\n"
                f"Профиль создан: {'да' if user_was_created else 'нет'}"
            )

            # Для админской выдачи важно синхронизировать ключи сразу после коммита подписки:
            # - новая подписка или продление без существующей подписки -> создание ключей
            # - продление существующей подписки -> включение/обновление ключей
            if issue_mode == "new" or not had_subscriptions_before_issue:
                asyncio.create_task(
                    create_keys_background(
                        user_id=user_id,
                        username=user.username or "",
                        subscription_id=subscription.subscription_id,
                        expiry_days=0,
                    )
                )
            else:
                asyncio.create_task(
                    update_keys_background(
                        user_id=user_id,
                        subscription_id=subscription.subscription_id,
                        status=True,
                    )
                )

            result_mode_text = "Создана новая отдельная подписка." if issue_mode == "new" else "Подписка продлена."
            if user_was_created:
                await message.answer(
                    'Пользователь отсутствовал в БД, профиль создан. '
                    + result_mode_text
                    + (' Пользователь уведомлён.' if notify_user else ' Выдано без уведомления.')
                )
            else:
                await message.answer(
                    result_mode_text
                    + (' Пользователь уведомлён.' if notify_user else ' Выдано без уведомления.')
                )

    except ValueError:
        await message.answer('Некорректные данные. Повторите команду.')
    except Exception as e:
        await logger.log_error("Ошибка при админской выдаче подписки", e)
        await message.answer("Не удалось выдать подписку. Проверьте логи и попробуйте снова.")

    await state.clear()
