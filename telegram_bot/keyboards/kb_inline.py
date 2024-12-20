from enum import Enum
from typing import Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.context_manager import DatabaseContextManager
from lexicon.lexicon_ru import LEXICON_RU
from logger.logging_config import logger
from models.models import NameApp, SubscriptionStatusEnum


class ServerCallbackData(CallbackData, prefix="server_disable"):
    action: str
    server_ip: str


class UserPaginationCallback(CallbackData, prefix="user"):
    page: int
    action: str


class UserSelectCallback(CallbackData, prefix="user_select"):
    action: str
    user_id: int


class ServiceCallbackFactory(CallbackData, prefix='service'):
    service_id: str
    status_pay: str


class UserInfoCallbackFactory(CallbackData, prefix='info'):
    action: str
    user_id: int
    ban: Optional[bool] = None
    trial: Optional[bool] = None


class SubscriptionCallbackFactory(CallbackData, prefix="subscription"):
    action: str
    subscription_id: Optional[int] = None
    name_app: Optional[str] = None


class ReplaceServerCallbackFactory(CallbackData, prefix="serv"):
    action: str
    subscription_id: Optional[int] = None
    server_ip: str


class ServerSelectCallback(CallbackData, prefix="servers"):
    server_ip: str
    server_name: str


class StarsPayCallbackFactory(CallbackData, prefix="stars_pay"):
    action: str
    service_id: str
    status_pay: str


class GuideSelectCallback(CallbackData, prefix="guide"):
    action: str
    name_oc: str
    name_app: str


class StatusPay(Enum):
    NEW = "new"
    OLD = "old"


class AutoRenewalCallbackFactory(CallbackData, prefix="auto_renewal"):
    action: str
    auto_renewal_enabled: Optional[bool] = None
    subscription_id: Optional[int] = None


class InlineKeyboards:
    @staticmethod
    async def create_order_keyboards(status_pay: StatusPay, back_target: str = None) -> InlineKeyboardMarkup:
        """Клавиатура для кнопок с услугами."""
        async with DatabaseContextManager() as session_methods:
            try:
                keyboard = InlineKeyboardBuilder()
                services = await session_methods.services.get_services()
                buttons: list[InlineKeyboardButton] = []

                for service in services:
                    service_id = str(service.service_id)
                    service_name = service.name

                    callback_data = ServiceCallbackFactory(
                        service_id=service_id,
                        status_pay=status_pay.value
                    ).pack()

                    buttons.append(InlineKeyboardButton(text=service_name, callback_data=callback_data))
                keyboard.row(*buttons)

                if back_target:
                    keyboard.row(
                        InlineKeyboardButton(text='🔙 Назад', callback_data=back_target)
                    )
                else:
                    keyboard.row(
                        InlineKeyboardButton(text='Отмена', callback_data='cancel')
                    )

                return keyboard.as_markup()
            except Exception as e:
                await logger.log_error(f'Произошла ошибка при формирование услуг', e)

    @staticmethod
    async def get_servers(ip, subscription_id) -> InlineKeyboardMarkup | int:
        async with DatabaseContextManager() as session_methods:
            try:
                keyboard = InlineKeyboardBuilder()
                servers = await session_methods.servers.get_all_servers()
                buttons: list[InlineKeyboardButton] = []

                for server in servers:
                    if server.hidden == 1:
                        continue
                    server_ip = server.server_ip
                    server_name = server.name

                    callback_data = ServerSelectCallback(
                        server_ip=server_ip,
                        server_name=server_name
                    ).pack()

                    buttons.append(InlineKeyboardButton(
                        text=server_name if server_ip != ip else server_name + "(Текущий)",
                        callback_data=callback_data))

                if len(buttons) == 0:
                    return 0
                keyboard.row(*buttons)

                keyboard.row(
                    InlineKeyboardButton(text='🔙 Назад', callback_data=f'view_details_{subscription_id}')
                )

                keyboard.adjust(1)

                return keyboard.as_markup()
            except Exception as e:
                await logger.log_error(f'Произошла ошибка при формирование услуг', e)

    @staticmethod
    async def create_pay(callback_data, price) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=f"Оплатить {price} ⭐️", pay=True)
        keyboard.button(
            text="🔙 Назад",
            callback_data=ServiceCallbackFactory(
                service_id=callback_data.service_id,
                status_pay=callback_data.status_pay
            ).pack()
        )

        keyboard.adjust(1, 2)

        return keyboard.as_markup()

    @staticmethod
    async def card_pay(callback_data):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Оплатить",
                    callback_data="empty"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=ServiceCallbackFactory(
                        service_id=callback_data.service_id,
                        status_pay=callback_data.status_pay
                    ).pack()
                )
            ]
        ])
        return keyboard

    @staticmethod
    async def payment_method(callback_data):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Картой",
                    callback_data=StarsPayCallbackFactory(
                        action="card_pay",
                        service_id=callback_data.service_id,
                        status_pay=callback_data.status_pay
                    ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="✨ Звездами",
                    callback_data=StarsPayCallbackFactory(
                        action="stars_pay",
                        service_id=callback_data.service_id,
                        status_pay=callback_data.status_pay
                    ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="back_to_services"
                )
            ]
        ])
        return keyboard

    @staticmethod
    async def get_support(callback_data: str = None) -> InlineKeyboardMarkup:
        support_user_id = "1"
        support_link = f"t.me/{support_user_id}"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать в поддержку",
                    url=support_link
                )
            ],
            [
                InlineKeyboardButton(
                    text="📜 Часто задаваемые вопросы",
                    callback_data="faq"
                )
            ]
        ])
        if callback_data:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=callback_data
                )
            ])
        else:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="🌌 Главное меню",
                    callback_data='back_to_start'
                )
            ])

        return keyboard

    @staticmethod
    async def cancel() -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text='Отменить', callback_data='cancel'))
        return keyboard.as_markup()

    @staticmethod
    async def menu_subs(subscription_id, name_app, server_ip):
        async with DatabaseContextManager() as session_methods:
            try:
                keyboard = InlineKeyboardBuilder()
                subscription = await session_methods.subscription.get_subscription_by_id(subscription_id)
                if subscription.status == SubscriptionStatusEnum.ACTIVE:
                    keyboard.add(
                        InlineKeyboardButton(
                            text='🌍 Изменить локацию',
                            callback_data=ReplaceServerCallbackFactory(
                                action='rep_serv',
                                subscription_id=subscription_id,
                                server_ip=server_ip
                            ).pack()),
                    )
                # Добавляем три кнопки с изменённым текстом
                keyboard.add(
                    InlineKeyboardButton(
                        text='⏳ Продлить подписку',
                        callback_data=SubscriptionCallbackFactory(
                            action='extend_subscription',
                            subscription_id=subscription_id
                        ).pack()),
                    InlineKeyboardButton(
                        text='Как подключиться ❔',
                        callback_data=SubscriptionCallbackFactory(
                            action='get_guide_install_app',
                            subscription_id=subscription_id,
                            name_app=name_app
                        ).pack()),
                    InlineKeyboardButton(
                        text='🔄 Автопродление',
                        callback_data=AutoRenewalCallbackFactory(
                            action='auto_renewal',
                            auto_renewal_enabled=False,
                            subscription_id=subscription_id,
                        ).pack()),
                    InlineKeyboardButton(
                        text='🔙 Назад',
                        callback_data='view_subs',
                    )
                )
                keyboard.adjust(2, 1)

                return keyboard.as_markup()
            except Exception as e:
                await logger.log_error(f'Произошла ошибка при формирование клавиатуры с подпиской', e)

    @staticmethod
    async def get_back_button_keyboard(callback: str = "back_to_support_menu") -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()

        back_button = InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=callback
        )

        keyboard.add(back_button)

        return keyboard.as_markup()

    @staticmethod
    async def get_guide(turn_on: str = None) -> InlineKeyboardMarkup:
        # Создаем клавиатуру с кнопкой "Инструкция"
        keyboard = InlineKeyboardBuilder()

        instruction_button = InlineKeyboardButton(
            text="Инструкция 📖",
            url=LEXICON_RU['outline_info']  # Ссылка на инструкцию
        )
        keyboard.add(instruction_button)

        if turn_on:
            back_button = InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_support_menu"
            )
            keyboard.add(back_button)

        keyboard.adjust(1)

        return keyboard.as_markup()

    @staticmethod
    async def create_user_pagination_with_users_keyboard(users, page: int, has_next: bool) -> InlineKeyboardMarkup:
        buttons = [[
            InlineKeyboardButton(text="Add all ✅", callback_data="add_all_users"),
            InlineKeyboardButton(text="Add subs ✅", callback_data="add_active_users")
        ]]

        # Кнопки для пользователей
        for user in users:
            buttons.append([InlineKeyboardButton(
                text=f"{user['username']} ({user['user_id']}) {'✅' if user['selected'] else ''}",
                callback_data=UserSelectCallback(
                    action="select",
                    user_id=user['user_id']).pack()
            )])

        # Кнопки пагинации
        pagination_buttons = [
            InlineKeyboardButton(text="⬅️ Назад",
                                 callback_data=UserPaginationCallback(
                                     page=page,
                                     action="previous").pack()) if page > 1 else InlineKeyboardButton(
                text="⬅️ Назад", callback_data="noop"),
            InlineKeyboardButton(text=f"{page}", callback_data="noop"),
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=UserPaginationCallback(
                    page=page,
                    action="next")
                .pack()) if has_next else InlineKeyboardButton(
                text="Вперед ➡️", callback_data="noop"),
        ]
        pagination_buttons = [button for button in pagination_buttons if button is not None]

        buttons.append(pagination_buttons)

        buttons.append([InlineKeyboardButton(text="Отменить всех ❌", callback_data="cancel_all")])
        buttons.append([InlineKeyboardButton(text="Сохранить", callback_data="save")])
        buttons.append([InlineKeyboardButton(text='Отменить', callback_data='cancel')])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    async def show_notify_change_cancel() -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()

        edit_message = InlineKeyboardButton(text="✏️ Изменить текст", callback_data="edit_message")
        send_notification = InlineKeyboardButton(text="📤 Отправить уведомление", callback_data="send_notification")
        cancel_button = InlineKeyboardButton(text='Отменить', callback_data='cancel')

        # Добавляем кнопки "Изменить текст" и "Отправить уведомление" в одну строку
        keyboard.add(edit_message, send_notification)
        # Вставляем кнопку "Отменить" в новую строку
        keyboard.add(cancel_button)

        # Настройка: максимум по две кнопки в строке
        keyboard.adjust(2)

        return keyboard.as_markup()

    @staticmethod
    async def replace_app(name_app, subscription_id) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        if name_app == NameApp.OUTLINE:
            button = InlineKeyboardButton(text="VLESS", callback_data=SubscriptionCallbackFactory(
                action='name_app', name_app="VLESS").pack())
        else:
            button = InlineKeyboardButton(text="OUTLINE", callback_data=SubscriptionCallbackFactory(
                action='name_app', name_app="OUTLINE").pack())
        keyboard.add(button)
        keyboard.row(
            InlineKeyboardButton(text='🔙 Назад', callback_data=f'view_details_{subscription_id}')
        )

        return keyboard.as_markup()

    @staticmethod
    async def show_guide(name_app) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        vless = InlineKeyboardButton(text="VLESS", callback_data=GuideSelectCallback(
            action='show_guide', name_oc=name_app, name_app='vless').pack())
        outline = InlineKeyboardButton(text="OUTLINE", callback_data=GuideSelectCallback(
            action='show_guide', name_oc=name_app, name_app='outline').pack())
        back = InlineKeyboardButton(text="Назад", callback_data=GuideSelectCallback(
            action='show_guide', name_oc=name_app, name_app='back').pack())
        keyboard.row(vless, outline)
        keyboard.add(back)
        keyboard.adjust(2, 1)

        return keyboard.as_markup()

    @staticmethod
    async def server_management_options(server_ip, hidden_status) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        if hidden_status == 0:
            show_status = InlineKeyboardButton(
                text="Выключить сервер",
                callback_data=ServerCallbackData(
                    action="disable",
                    server_ip=server_ip
                ).pack()
            )
        else:
            show_status = InlineKeyboardButton(
                text="Включить сервер",
                callback_data=ServerCallbackData(
                    action="enable",
                    server_ip=server_ip
                ).pack()
            )
        server_name = InlineKeyboardButton(
            text="Изменить имя",
            callback_data=ServerCallbackData(
                action="change_name",
                server_ip=server_ip
            ).pack()
        )
        server_limit = InlineKeyboardButton(
            text="Изменить лимит",
            callback_data=ServerCallbackData(
                action="change_limit",
                server_ip=server_ip
            ).pack()
        )
        keyboard.add(show_status, server_name, server_limit)

        return keyboard.as_markup()

    @staticmethod
    async def get_trial_subscription_keyboard():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚔️ Активировать подписку",
                    callback_data="activate_trial"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="back_to_start"
                )
            ]
        ])
        return keyboard

    @staticmethod
    async def get_subscriptions_keyboard():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🐉 Мои подписки",
                    callback_data="view_subs"
                )
            ]
        ])
        return keyboard

    @staticmethod
    async def get_menu_keyboard():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🐲 Пробный период",
                    callback_data="trial_subs"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌌 Главное меню",
                    callback_data="main_menu"
                )
            ],
        ],
        )
        return keyboard

    @staticmethod
    async def get_invite_keyboard(callback_data: str = None):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🐲 Приглашенные друзья",
                    callback_data="show_referrals"
                ),
                InlineKeyboardButton(
                    text="🔗 Пригласить друга",
                    callback_data="get_invite_link"
                )
            ]
        ])

        # Добавляем кнопку "Назад" при наличии callback_data
        if callback_data:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=callback_data
                )
            ])

        return keyboard

    @staticmethod
    async def get_back_to_faq_keyboard(faq_key):
        if faq_key in ["faq_change_app", "faq_change_territory", "faq_slow_internet"]:
            return InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🐉 Мои подписки",
                        callback_data="view_subs"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Вернуться в меню FAQ",
                        callback_data="faq"
                    )
                ]
            ])
        elif faq_key == 'faq_install_amulet':
            return InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🐉 Мои подписки",
                        callback_data="view_subs"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Вернуться в меню FAQ",
                        callback_data="faq"
                    )
                ]
            ])
        elif faq_key == 'faq_payment':
            return InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔥 Оформить подписку",
                        callback_data="subscribe"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Вернуться в меню FAQ",
                        callback_data="faq"
                    )
                ]
            ])

    @staticmethod
    async def get_faq_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌍 Сменить локацию",
                    callback_data="faq_change_territory"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧿 Сменить приложение",
                    callback_data="faq_change_app"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Оформить подписку",
                    callback_data="faq_payment"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚡ VPN плохо работает",
                    callback_data="faq_slow_internet"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔮 Как установить",
                    callback_data="faq_install_amulet"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="support_callback"
                )
            ]
        ])

    @staticmethod
    async def get_menu_install_app(name_app, subscription_id) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Android 📱",
                    callback_data=SubscriptionCallbackFactory(
                        action='Android',
                        subscription_id=subscription_id,
                        name_app=name_app
                    ).pack()),
                InlineKeyboardButton(
                    text="iPhone 🍏",
                    callback_data=SubscriptionCallbackFactory(
                        action='iPhone',
                        subscription_id=subscription_id,
                        name_app=name_app
                    ).pack())
            ],
            [
                InlineKeyboardButton(
                    text="Windows 💻",
                    callback_data=SubscriptionCallbackFactory(
                        action='Windows',
                        subscription_id=subscription_id,
                        name_app=name_app
                    ).pack()),
                InlineKeyboardButton(
                    text="MacOS 💻",
                    callback_data=SubscriptionCallbackFactory(
                        action='MacOS',
                        subscription_id=subscription_id,
                        name_app=name_app
                    ).pack())
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data=f"view_details_{subscription_id}")
            ],
        ])
        return keyboard

    @staticmethod
    async def user_info(user_id, ban, trial):
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Разбанить" if ban else "Забанить",
                    callback_data=UserInfoCallbackFactory(
                        action="user_ban",
                        user_id=user_id,
                        ban=not ban
                    ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="Обновить",
                    callback_data=UserInfoCallbackFactory(
                        action="user_trial",
                        user_id=user_id,
                        trial=not trial
                    ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="Подписки пользователя",
                    callback_data=UserSelectCallback(
                        action='user_subs',
                        user_id=user_id
                    ).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data="cancel"
                )
            ]
        ])

    @staticmethod
    async def sub_info(user_id):
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Дата окончания",
                    callback_data=UserSelectCallback(
                        action='end_date_sub',
                        user_id=user_id
                    ).pack())
            ],
            [
                InlineKeyboardButton(
                    text="Выключить подписку",
                    callback_data=UserSelectCallback(
                        action='turn_off_sub',
                        user_id=user_id
                    ).pack())
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data=''
                )
            ],
        ])

    @staticmethod
    async def main_menu():
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🐉 Мои подписки",
                    callback_data="view_subs"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔥 Оформить подписку",
                    callback_data="subscribe"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Пригласить друга",
                    callback_data="back_to_call_allies"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧙‍♂️ Поддержка",
                    callback_data="help_wizards_callback"
                )
            ],
        ]
        )

    @staticmethod
    async def get_user_info(user_id: int):
        user_link = f"tg://user?id={user_id}"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Пользователь",
                        url=user_link
                    )
                ]
            ]
        )
        return keyboard

    @staticmethod
    async def create_or_extend():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🐉 Мои подписки",
                    callback_data="view_subs"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔥 Оформить подписку",
                    callback_data="create_order"
                )
            ],
        ],
        )
        return keyboard
