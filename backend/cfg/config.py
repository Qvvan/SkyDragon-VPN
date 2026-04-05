from environs import Env

env = Env()
env.read_env()

DSN = env.str("DSN")
CRYPTO_KEY = env.str("CRYPTO_KEY")

# Публичный URL сайта (ссылки в подписке Happ, импорт). Без слэша в конце.
PUBLIC_BASE_URL = env.str("PUBLIC_BASE_URL", "https://skydragonvpn.ru").rstrip("/")
TELEGRAM_BOT_URL = env.str("TELEGRAM_BOT_URL", "https://t.me/SkyDragonVPNBot").rstrip("/")
TELEGRAM_SUPPORT_URL = env.str("TELEGRAM_SUPPORT_URL", "https://t.me/SkyDragonSupport").rstrip("/")
TELEGRAM_BOT_START_1 = f"{TELEGRAM_BOT_URL}?start=1"
TELEGRAM_YOOKASSA_RETURN_URL = env.str("TELEGRAM_YOOKASSA_RETURN_URL", "").strip() or TELEGRAM_BOT_URL

SUB_PORT = env.int("SUB_PORT", 2096)
# Порт панели 3x-ui на сервере (если не задан в сервере)
PORT_X_UI = env.int("PORT_X_UI", 443)
# Путь панели (для подписки /path/sub/...), по умолчанию из env
MY_SECRET_URL = env.str("MY_SECRET_URL", "mysecreturl")
SHOP_ID = env.str("SHOP_ID", "")
SHOP_API_TOKEN = env.str("SHOP_API_TOKEN", "")