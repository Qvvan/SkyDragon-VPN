from environs import Env

env = Env()
env.read_env()

DSN = env.str("DSN")
CRYPTO_KEY = env.str("CRYPTO_KEY")
SUB_PORT = env.int("SUB_PORT", 2096)