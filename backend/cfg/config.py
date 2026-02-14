from environs import Env

env = Env()
env.read_env()

DSN = env.str("DSN")
CRYPTO_KEY = env.str("CRYPTO_KEY")
SUB_PORT = env.int("SUB_PORT", 2096)
# Порт панели 3x-ui на сервере (если не задан в сервере)
PORT_X_UI = env.int("PORT_X_UI", 443)
# Путь панели (для подписки /path/sub/...), по умолчанию из env
MY_SECRET_URL = env.str("MY_SECRET_URL", "mysecreturl")