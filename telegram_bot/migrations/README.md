# Миграции БД телеграм-бота

## Как применить миграцию `20260213_01_add_server_api_fields.sql`

Миграция добавляет в таблицу `servers` поля: `available_ports`, `panel_port`, `url_secret`.

### Способ 1: через psql (рекомендуется)

Если есть доступ к консоли PostgreSQL:

```bash
# Из строки подключения DSN (скопируйте из .env)
psql "postgresql://USER:PASSWORD@HOST:PORT/DATABASE" -f migrations/20260213_01_add_server_api_fields.sql
```

Или по шагам:

```bash
psql -h HOST -p PORT -U USER -d DATABASE -f migrations/20260213_01_add_server_api_fields.sql
```

Подставьте `HOST`, `PORT`, `USER`, `DATABASE` и пароль из вашего `.env` (или переменные `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_NAME`, `DB_PASSWORD`).

### Способ 2: через Python-скрипт

Из корня репозитория (папка `SkyDragon-VPN`):

```bash
cd telegram_bot
python scripts/apply_migration.py
```

Или из папки `telegram_bot`:

```bash
python -m scripts.apply_migration
```

Нужно, чтобы в `.env` был задан `DSN` (или `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`). Для скрипта нужна одна из библиотек: `psycopg2-binary` или `asyncpg`.

```bash
pip install psycopg2-binary
# или
pip install asyncpg
```

### Способ 3: вручную в клиенте БД

Откройте файл `migrations/20260213_01_add_server_api_fields.sql` в DBeaver, pgAdmin или другом клиенте и выполните его SQL против нужной базы.

---

После применения миграции перезапустите бота.
