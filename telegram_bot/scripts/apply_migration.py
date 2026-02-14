#!/usr/bin/env python3
"""
Применяет SQL-миграцию к базе данных телеграм-бота.
Использует DSN из переменных окружения (.env) или config.

Запуск из корня проекта:
  python -m scripts.apply_migration
  или из папки telegram_bot:
  python scripts/apply_migration.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Добавляем корень telegram_bot в путь
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Загружаем .env
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# DSN может быть в формате postgresql://... или postgresql+asyncpg://...
def get_psycopg_dsn():
    """Преобразует DSN в формат для psycopg (sync) или возвращает компоненты."""
    host = "localhost"
    port = 5442
    dbname = "vpn_bot_tg"
    user = "vpn_bot_tg"
    password = "1asDS2d3QBDF9Wew4WEqzx45DF3vG6FDdk9QWxo3GDU123"
    if all([user, password, host, dbname]):
        return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    return None


def run_migration_sync():
    """Применяет миграцию через psycopg2 (синхронно)."""
    try:
        import psycopg2
    except ImportError:
        print("Установите psycopg2: pip install psycopg2-binary")
        return False

    dsn = get_psycopg_dsn()
    if not dsn:
        print("Не задан DSN. Укажите DSN в .env или переменные DB_USER, DB_PASSWORD, DB_HOST, DB_NAME.")
        return False

    migration_file = ROOT / "migrations" / "20260213_01_add_server_api_fields.sql"
    if not migration_file.exists():
        print(f"Файл миграции не найден: {migration_file}")
        return False

    sql = migration_file.read_text(encoding="utf-8")
    print(f"Применяю миграцию: {migration_file.name}")

    try:
        conn = psycopg2.connect(dsn)
        conn.autocommit = False
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
        print("Миграция применена успешно.")
        return True
    except Exception as e:
        print(f"Ошибка применения миграции: {e}")
        return False


async def run_migration_async():
    """Применяет миграцию через asyncpg (если DSN с asyncpg)."""
    try:
        import asyncpg
    except ImportError:
        return run_migration_sync()

    dsn = os.getenv("DSN")
    if not dsn:
        return run_migration_sync()

    # Оставляем asyncpg DSN как есть
    if "+asyncpg" not in dsn and dsn.startswith("postgresql://"):
        dsn = dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
    if dsn.startswith("postgresql+asyncpg://"):
        dsn = dsn.replace("postgresql+asyncpg://", "postgresql://", 1)

    migration_file = ROOT / "migrations" / "20260213_01_add_server_api_fields.sql"
    if not migration_file.exists():
        print(f"Файл миграции не найден: {migration_file}")
        return False

    sql = migration_file.read_text(encoding="utf-8")
    print(f"Применяю миграцию: {migration_file.name}")

    try:
        conn = await asyncpg.connect(dsn)
        # asyncpg execute поддерживает несколько команд в одной строке
        await conn.execute(sql)
        await conn.close()
        print("Миграция применена успешно.")
        return True
    except Exception as e:
        print(f"Ошибка применения миграции: {e}")
        return False


if __name__ == "__main__":
    if sys.version_info >= (3, 7) and hasattr(asyncio, "run"):
        # Пробуем asyncpg, при неудаче — sync
        try:
            ok = asyncio.run(run_migration_async())
        except Exception:
            ok = run_migration_sync()
    else:
        ok = run_migration_sync()
    sys.exit(0 if ok else 1)
