from environs import Env

env = Env()
env.read_env()

DSN = env.str("DSN")

CRYPTO_KEY = env.str("CRYPTO_KEY")

# Совпадает с backend/cfg/config.py — ссылки в боте и в подписке должны указывать на тот же стенд.
PUBLIC_BASE_URL = env.str("PUBLIC_BASE_URL", "https://skydragonvpn.ru").rstrip("/")
TELEGRAM_BOT_URL = env.str("TELEGRAM_BOT_URL", "https://t.me/SkyDragonVPNBot").rstrip("/")
TELEGRAM_SUPPORT_URL = env.str("TELEGRAM_SUPPORT_URL", "https://t.me/SkyDragonSupport").rstrip("/")
TELEGRAM_SUPPORT_USERNAME = env.str("TELEGRAM_SUPPORT_USERNAME", "SkyDragonSupport")
TELEGRAM_YOOKASSA_RETURN_URL = env.str("TELEGRAM_YOOKASSA_RETURN_URL", "").strip() or TELEGRAM_BOT_URL

ADMIN_IDS = [int(admin) for admin in env.list('ADMIN_IDS')]

BOT_TOKEN = env.str("BOT_TOKEN")
TELEGRAM_PROXY = env.str("TELEGRAM_PROXY", "")

ERROR_GROUP_ID = env.int("ERROR_GROUP_ID")
INFO_GROUP_ID = env.int("INFO_GROUP_ID")
ONLINE_ABUSE_CHAT_ID = env.int("ONLINE_ABUSE_CHAT_ID", 0)

MY_SECRET_URL = env.str("MY_SECRET_URL", "mysecreturl")
LOGIN_X_UI_PANEL = env.str("LOGIN_X_UI_PANEL", "admin")
PASSWORD_X_UI_PANEL = env.str("PASSWORD_X_UI_PANEL", "admin")
PORT_X_UI = env.int("PORT_X_UI", 54321)

SHOP_ID = env.str("SHOP_ID")
SHOP_API_TOKEN = env.str("SHOP_API_TOKEN")

INN = env.str("INN")
PASSWORD_MY_NALOG = env.str("PASSWORD_MY_NALOG")

SOURCE_DEVICE_ID = env.str("SOURCE_DEVICE_ID")