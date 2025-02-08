from environs import Env

env = Env()
env.read_env()

DSN = env.str("DSN")
CRYPTO_KEY = env.str("CRYPTO_KEY")