LEXICON_COMMANDS: dict[str, str] = {
    '/new': 'Оформить подписку 🐉',
    '/profile': 'Мои подписки 🛡️',
    '/friends': 'Позвать друга 🏰',
    '/help': 'Помощь хранителей 🧙‍♂️',
}

LEXICON_COMMANDS_ADMIN: dict[str, str] = {
    '/add_server': 'Добавить сервер в базу данных',
    '/show_servers': 'Управление серверами',
    '/pushes': 'Можно отправить уведомления пользователям',
    '/add_key': 'Добавить ключ в базу данных',
    '/del_key': 'Удалить ключ',
    '/block_key': 'Заблокировать ключ',
    '/unblock_key': 'Разблокировать ключ',
    '/key_info': 'Получить информацию о ключе',
    # /user_info': 'Получить информацию о пользователе по Telegram ID',
    '/ban_user': 'Забанить пользователя по Telegram ID',
    '/unban_user': 'Разбанить пользователя по Telegram ID',
    '/cancel_sub': 'Отменить подписку пользователя по ID',
    '/refund': 'Возврат средств пользователю по транзакции',
    '/shutdown': 'Выключить бота',
    '/run_bot': 'Включить бота',
}

LEXICON_RU: dict[str, str] = {
    "legend": (
        "Когда-то давно, в скрытых мирах за гранью человеческого понимания, существовали великие драконы 🐉 — хранители знаний 📜 и защитники древних тайн. Эти драконы, известные как Драконы Сокрытых Сфер, веками оберегали потоки информации, защищая их от тёмных сил ⚔️, что пытались захватить власть над истиной.\n\n"
        "Среди них были четыре великих дракона: мудрый *Шааргос* 🐲, могучий *Валдрим* 🛡️, огненный *Сангрил* 🔥 и легендарный *Элдрагон* 👑. Каждый из них обладал уникальной силой защиты. Шааргос открывал путь к тайнам на короткий срок, Валдрим создавал защитные барьеры на долгие месяцы, Сангрил наделял свои амулеты силой огня 🔥, а Элдрагон — самый древний и могущественный из всех — дарил защиту, что не знала преград во времени 🌌.\n\n"
        "Но мир изменился, и древние знания стали уязвимы для цифровых угроз 👾. Чтобы сохранить наследие драконов и продолжить их миссию, была создана *SkyDragon VPN* — цифровая броня 🛡️, в которой заключены силы всех четырёх драконов. *SkyDragon* теперь оберегает пользователей, словно древний дракон над кладом знаний, помогая им безопасно путешествовать по миру информации 🌐.\n\n"
        "Присоединившись к *SkyDragon VPN*, каждый обретает защиту этих мифических существ 🐲, ведь в цифровой эпохе древняя магия ✨ живёт и защищает, как и прежде."
    ),
    "start": (
        "Добро пожаловать в *SkyDragon VPN*! 🐉\n\n"
        "🐲 *Пробная подписка*: *7-дневный пробный период*\n\n"
        "🎁 За каждого приглашённого Вы получите до *30 дней* бесплатной подписки!\n\n"
    ),
    "createorder": (
        " <b>SkyDragon VPN</b> – Защита, рожденная в легендах драконов 🐉\n\n"
        "🐲 <b>Шааргос</b> – <i><u>1 месяц</u>  защиты 49</i> ⭐\n"
        "🐉 <b>Валдрим</b> – <i><u>3 месяца</u> защиты 130</i> ⭐ (<i>экономия 10%</i>)\n"
        "🔥 <b>Сангрил</b> – <i><u>6 месяцев</u> защиты 230</i> ⭐ (<i>экономия 20%</i>)\n"
        "👑 <b>Элдрагон</b> – <i><u>12 месяцев</u> защиты 402</i> ⭐ (<i>экономия 30%</i>)\n\n"
        "<i>1 звезда ⭐ ~ 2.09 рубля ₽</i>"
    ),
    "purchase_thank_you": (
        "🔥 Благодарим за доверие, путник!\n"
        "🐉 Твой SkyDragon VPN активирован!\n\n"
    ),

    "subscription_renewed": (
        "🙏 Благодарим за верность легенде!\n"
        "🔄 Твоя подписка продлена! 🛡️\n\n"
    ),

    "error": (
        "⚠️ Драконы встретили преграду. Попробуйте позже или обратитесь к нашему проводнику в поддержку /help."
    ),

    "not_exists": (
        "😔 К сожалению, ты пока не обрел защиту древних драконов... "
        "Активируй подписку и вступи в наш круг силы."
    ),

    "refund_message": (
        "✅ Транзакция отменена! 💰 Средства возвращены на твой счёт. "
        "Благодарим за то, что остаёшься под защитой SkyDragon!"
    ),

    "expired": (
        "🕒 Ваша защита истекла.\n\n"
        "Чтобы продолжить пользоваться SkyDragon VPN, продли свою подписку и вернись под защиту драконов. 🛡️🔥"
    ),

    "reminder_sent": (
        "⚠️ <b>Внимание, путник!</b> ⚠️\n\n"
        "📅 <b>Твоя подписка</b> истекает через <b>3 дня</b>!\n"
        "⏳ Продли её, чтобы сохранить доступ к силе драконов и остаться под надёжной защитой.\n\n"
    ),
    "choice_app": (
        "🧿 <b>Сейчас у вас приложение {current_app}</b>\n\n"
        "Если соединение нестабильно и смена локации не помогает, "
        "попробуйте сменить приложение на {new_app}.\n\n"
    ),
    "invite": (
        "🐲 Пригласите друга в наше логово драконов, отправив ему эту ссылку:\n"
        "{referral_link}\n\n"
        "🌟 Когда ваш друг присоединится, вы обретёте силу древних и получите бонус!"
    ),

    "invite_info": (
        "📜 Здесь вы можете узнать количество приведённых друзей или призвать нового!\n\n"
        "🎁 За каждого друга, присоединившегося к нам, вы получаете 7 дней защиты под крылом дракона.\n"
        "👑 Если ваш друг оплатит подписку, вам начислятся ещё 23 дня драконьей защиты!"
    ),

    "referrer_message": (
        "🐉 Ваш союзник, @{username}, оформил подписку.\n"
        "Вы получаете дополнительную защиту в 23 дня — дар древних драконов! 🎁\n"
    ),

    "trial_activated": (
        "🎉 Ваша пробная защита активирована! Драконы даруют вам 7 дней защиты."
    ),
    "trial_subscription_used": (
        "⚠️ Пробная подписка уже использована.\n\n"
        "Чтобы продолжить пользоваться силой драконов, выберите подходящий тариф в личном кабинете.\n\n"
        "🔔 В случае вопросов, поддержка всегда на страже, готова помочь вам!"
    ),
    "subscription_not_found": (
        "🔑 Ты не оформил подписку. Чтобы получить силу дракона, "
        "оформи подписку.\n\n"
    ),

    "trial_offer": (
        "🌌 Вы еще не воспользовались пробной защитой под крылом дракона.\n\n"
        "Воспользуйтесь бесплатной пробной защитой на 7 дней.\n\n"
        "🔮 Нажмите кнопку ниже, чтобы активировать защиту и начать путь уже сегодня! 👇"
    ),
    "no_invites": (
        "🐉 Пока никто не присоединился к вашему кругу под защитой драконов.\n\n"
        "📜 Пригласите друга, чтобы вместе обрести силу древних и получить дополнительные дни защиты!"
    ),
    "no_servers_available": (
        "😔 Увы, доступные владения драконов не найдены.\n"
        "Пожалуйста, попробуйте позже.\n"
        "Драконы восстанавливают свои силы, чтобы защитить вас снова! 🐉"
    ),
    "choose_location": (
        "Смена локации VPN может помочь улучшить качество интернета"
    ),
    "subscription_not_found_error": (
        "🐲 Дракон не найден среди ваших защитников. Пожалуйста, попробуйте снова."
    ),
    "location_changed_success": (
        "🏞️ Локация успешно изменена на {selected_server_name}.\n"
        "🐲 Ваш ключ:\n"
        "<pre>{key}</pre>"
    ),
    "choose_device": (
        "Настройки успешно обновлены! Если требуется помощь с подключением, выберите своё устройство 👇, "
        "и я покажу путь к обретению силы под защитой драконов 🐉"
    ),
    "server_unavailable": (
        "⚠️ Эта локация временно закрыта для доступа. Пожалуйста, выберите другую локацию под защитой драконов."
    ),
    "app_changed_success": (
        "🧿 Приложение успешно изменено на {name_app}.\n"
        "🐉 Ваш ключ:\n"
        "<pre>{key}</pre>"
    ),
    "purchase_cancelled": (
        "🐉 К сожалению, что-то пошло не так...\n"
        "⚔️ Скоро к вам обратится техподдержка‍ ️🧙‍♂️"
    ),
    "help_message": (
        "🧙‍♂️ Приветствую, путник!\n\n"
        "Ты обратился к хранителям — магам, которые обеспечивают защиту и помогают тем, кто ищет ответ. "
        "Как только хранители услышат твой запрос, они немедленно откроют для тебя путь к решению.\n\n"
        "⚔️ Чем могу помочь? Напиши свой запрос, и я передам его нашим мудрым хранителям."
    ),
    "faq_install_amulet": (
        "🔮 Как установить амулет на своё орудие?\n\n"
        "Чтобы установить амулет, выбери устройство, которое ты используешь как орудие. "
        "Амулет будет подключён к твоему орудию, и дракон начнёт охранять тебя через этот магический артефакт.\n"
        "⚔️ Просто выбери орудие и следуй за указаниями, чтобы установить амулет!"
    ),
    "faq_slow_internet": (
        "⚡ Что если защита дракона работает медленно?\n\n"
        "Если твой интернет не даёт драконьей силы, попробуй изменить амулет или выбери новую территорию для защиты. "
        "Иногда дракон может быть слишком далёк, и нужно сменить местоположение для лучшего подключения!\n"
        "🔄 Проверь соединение и выбери более подходящее местоположение!"
    ),
    "faq_payment": (
        "💎 Как оплатить за продолжение защиты?\n\n"
        "Чтобы продлить защиту, необходимо выбрать подходящий обет и активировать его через амулет. "
        "Дракон продолжит охранять тебя в обмен на волшебные средства — твои средства будут преобразованы в силу!\n"
        "⚡ Просто выбери подходящий обет, и защита будет продлена!"
    ),
    "faq_change_app": (
        "🧿 Как сменить амулет (приложение)?\n\n"
        "Чтобы сменить амулет, просто выбери другой из предложенных. "
        "Это изменит силу твоего дракона и защиту, предоставляемую им. "
        "Просто выбери новый амулет и почувствуй силу изменений!"
    ),
    "faq_change_territory": (
        "🌍 Как сменить территорию дракона?\n\n"
        "Чтобы изменить территорию, выбери новое местоположение для своего дракона. "
        "Дракон переместит свою защиту в новое место, и ты получишь доступ к новому региону.\n"
        "🔑 Просто выбери новое место, и защита будет перенесена!"
    ),
    "faq_intro": (
        "Ты оказался в месте, где древние вопросы находят свои ответы. "
        "Выбери один из вопросов ниже, и хранители откроют тебе двери в мир знаний и магии.\n\n"
        "Что интересует тебя на пути защиты?"
    ),
    "text_dragons_overview": (
        "🐉 <b>Твой дракон и его сила</b>\n\n"
        "🔄 <b>Изменить цитадель</b> – если интернет работает нестабильно, выбери новое местоположение для VPN-сервера, "
        "чтобы улучшить соединение.\n\n"
        "🧿 <b>Изменить амулет</b> – выбери другое приложение для подключения к VPN, если возникают трудности с доступом.\n\n"
        "🐲🔑 <b>Имя дракона</b> – твой уникальный ключ для активации защиты. Вставь его в приложение, чтобы подключиться к VPN."
    ),
    "intro_text": (
        "🐉 <b>Твои подписки</b>\n\n"
    ),
    "subscription_expired": (
        "К сожалению, вы не можете поменять локацию, так как ваша подписка истекла."
    ),
    "main_menu": (
        "🐉 *Главное меню*\n\n"
    )

}

guide_install = {
    "Vless": {
        "iPhone": "🐉 **Как установить защиту дракона на iPhone:**\n\n"
                  "🐲 Ключ доступа\n`{key}`\n\n"
                  "1️⃣ Скопируй ключ, просто нажав на него🔑\n"
                  "2️⃣ Установи приложение [Streisand](https://apps.apple.com/ru/app/streisand/id6450534064) из AppStore\n"
                  "3️⃣ Открой приложение Streisand и нажми на ➕ в правом верхнем углу\n"
                  "4️⃣ Выбери «Добавить из буфера» для подключения\n"
                  "5️⃣ Нажми на кнопку включения и ощути защиту древнего покровительства! 🌐✨",

        "Android": "🐉 **Как установить защиту дракона на Android:**\n\n"
                  "🐲 Ключ доступа\n`{key}`\n\n"
                  "1️⃣ Скопируй ключ, просто нажав на него🔑\n"
                   "2️⃣ Установи амулет [V2rayNG](https://play.google.com/store/apps/details?id=com.v2ray.ang&hl=ru) из Google Play\n"
                   "3️⃣ Открой приложение V2rayNG и нажми на ➕ в правом верхнем углу\n"
                   "4️⃣ Выбери «Импорт из буфера обмена», чтобы призвать силу дракона\n"
                   "5️⃣ Нажми на кнопку включения и почувствуй покровительство древних 🌐✨",

        "Windows": "🐉 **Как установить защиту дракона на Windows:**\n\n"
                   "🐲 Ключ доступа\n`{key}`\n\n"
                   "1️⃣ Скопируй ключ, просто нажав на него🔑\n"
                   "2️⃣ Скачай с [GitHub](https://github.com/hiddify/hiddify-next/releases)\n"
                   "3️⃣ Для Windows выбери версию Portable или Setup\n"
                   "4️⃣ Запусти программу с правами администратора для активации\n"
                   "5️⃣ Выбери свой регион\n"
                   "6️⃣ Вставь подписку, выбрав «Новый профиль» > «Добавить профиль из буфера обмена»\n"
                   "7️⃣ Наслаждайся защитой древнего покровительства в цифровых просторах 🌐✨",

        "MacOS": "🐉 **Как установить защиту дракона на MacOS:**\n\n"
                 "🐲 Ключ доступа\n`{key}`\n\n"
                 "1️⃣ Скопируй ключ, просто нажав на него🔑\n"
                 "2️⃣ Установи приложение [V2Box](https://apps.apple.com/ru/app/v2box-v2ray-client/id6446814690) из AppStore\n"
                 "3️⃣ Открой V2Box и перейди во вкладку «Configs»\n"
                 "4️⃣ Нажми ➕ в правом верхнем углу и выбери «Import v2ray uri from clipboard»\n"
                 "5️⃣ Перейди на вкладку «Home» и нажми на большую кнопку «Tap to Connect» для активации защиты\n"
                 "6️⃣ Наслаждайся охраной дракона и безопасным интернетом 🌐✨",

    },
    "Outline": {
        "iPhone": "🐉 *Как установить защиту дракона на iPhone:*\n\n"
                  "🐲 Ключ доступа\n`{key}`\n\n"
                  "1️⃣ Скопируй ключ, просто нажав на него🔑\n"
                  "2️⃣ Установи приложение [Outline](https://apps.apple.com/ru/app/outline-app/id1356177741) из AppStore\n"
                  "3️⃣ Открой Outline и вставь ключ, нажав на значок ➕ в правом верхнем углу\n"
                  "4️⃣ Нажми `Подключиться`, чтобы ощутить силу древнего покровительства! 🌐✨",

        "Android": "🐉 *Как установить защиту дракона на Android:*\n\n"
                  "🐲 Ключ доступа\n`{key}`\n\n"
                  "1️⃣ Скопируй ключ, просто нажав на него🔑\n"
                   "2️⃣ Установи приложение [Outline](https://play.google.com/store/apps/details?id=org.outline.android.client&hl=ru) из Google Play\n"
                   "3️⃣ Открой Outline и вставь ключ, нажав на значок ➕ в правом верхнем углу\n"
                   "4️⃣ Нажми `Подключиться`, чтобы обрести покровительство дракона. Пусть твоё соединение будет быстрым и стабильным 🌐✨",

        "Windows": "🐉 *Как установить защиту дракона на Windows:*\n\n"
                  "🐲 Ключ доступа\n`{key}`\n\n"
                  "1️⃣ Скопируй ключ, просто нажав на него🔑\n"
                   "2️⃣ Скачай приложение [Outline](https://s3.amazonaws.com/outline-releases/client/windows/stable/Outline-Client.exe) и установи его\n"
                   "3️⃣ Открой Outline и вставь ключ, нажав на значок ➕ в правом верхнем углу\n"
                   "4️⃣ Нажми `Подключиться`, чтобы ощутить защиту древнего покровительства. Пусть твой путь в сети будет защищён 🌐✨",

        "MacOS": "🐉 *Как установить защиту дракона на MacOS:*\n\n"
                 "🐲 Ключ доступа\n`{key}`\n\n"
                 "1️⃣ Скопируй ключ, просто нажав на него🔑\n"
                 "2️⃣ Установи приложение [Outline](https://apps.apple.com/us/app/outline-secure-internet-access/id1356178125?mt=12) из App Store\n"
                 "3️⃣ Открой Outline и вставь ключ, нажав на значок ➕ в правом верхнем углу\n"
                 "4️⃣ Нажми `Подключиться`, чтобы активировать покровительство дракона. 🌐✨",

    }
}
