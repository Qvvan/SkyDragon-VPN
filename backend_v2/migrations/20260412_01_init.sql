-- depends:

-- ── Subscriptions ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id         BIGINT      NOT NULL,
    service_id      INTEGER     NULL,
    start_date      TIMESTAMP   NULL,
    end_date        TIMESTAMP   NULL,
    status          VARCHAR(64) NULL,
    reminder_sent   INTEGER     NOT NULL DEFAULT 0,
    auto_renewal    BOOLEAN     NOT NULL DEFAULT TRUE,
    card_details_id VARCHAR(255) NULL,
    account_id      UUID        NULL,
    created_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id
    ON subscriptions (user_id);

CREATE INDEX IF NOT EXISTS idx_subscriptions_account_id
    ON subscriptions (account_id)
    WHERE account_id IS NOT NULL;

-- ── Servers ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS servers (
    server_id       SERIAL PRIMARY KEY,
    server_ip       VARCHAR(255) NOT NULL,
    name            VARCHAR(255) NOT NULL,
    "limit"         INTEGER NULL,
    hidden          INTEGER NOT NULL DEFAULT 0,
    available_ports VARCHAR(255) NULL,
    panel_port      INTEGER NULL,
    url_secret      VARCHAR(255) NULL,
    sub_port        INTEGER NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_servers_server_ip ON servers (server_ip);

-- ── Services ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS services (
    service_id     SERIAL PRIMARY KEY,
    name           VARCHAR(100) NOT NULL,
    description    TEXT,
    duration_days  INTEGER NOT NULL,
    price          NUMERIC(10, 2) NOT NULL,
    original_price NUMERIC(10, 2),
    is_trial       BOOLEAN NOT NULL DEFAULT FALSE,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    is_featured    BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order     INTEGER NOT NULL DEFAULT 0,
    badge          VARCHAR(50),
    created_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_services_active_sort
    ON services (sort_order)
    WHERE is_active = TRUE;

-- Seed: пробный + 4 платных плана
INSERT INTO services (name, duration_days, price, is_trial, is_active, sort_order) VALUES
    ('Пробный период', 5,   0,    TRUE,  TRUE, 0),
    ('30 дней',        30,  100,  FALSE, TRUE, 1),
    ('90 дней',        90,  285,  FALSE, TRUE, 2),
    ('180 дней',       180, 570,  FALSE, TRUE, 3),
    ('360 дней',       360, 1120, FALSE, TRUE, 4);

-- ── Payments ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS payments (
    id                UUID         NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    payment_id        VARCHAR(255) NOT NULL UNIQUE,
    user_id           BIGINT       NOT NULL DEFAULT 0,
    account_id        UUID         NULL,
    recipient_user_id BIGINT       NULL,
    service_id        INTEGER      NULL,
    status            VARCHAR(64)  NOT NULL DEFAULT 'pending',
    payment_type      VARCHAR(64)  NULL DEFAULT 'myself',
    receipt_link      VARCHAR(1024) NULL,
    created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Accounts ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS accounts (
    id            UUID         NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    login         VARCHAR(64)  NOT NULL,
    password_hash TEXT         NOT NULL,
    first_name    VARCHAR(128) NOT NULL DEFAULT '',
    last_name     VARCHAR(128) NOT NULL DEFAULT '',
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_login
    ON accounts (login);

-- ── Account ↔ Telegram links ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS account_telegram_links (
    telegram_user_id BIGINT PRIMARY KEY,
    account_id       UUID   NOT NULL REFERENCES accounts (id) ON DELETE CASCADE,
    linked_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_account_telegram_links_one_tg_per_account UNIQUE (account_id)
);

CREATE INDEX IF NOT EXISTS idx_account_telegram_links_account_id
    ON account_telegram_links (account_id);

-- ── Deferred FK constraints (reference accounts which is defined above) ──

ALTER TABLE subscriptions
    ADD CONSTRAINT fk_subscriptions_account_id
    FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE SET NULL;

ALTER TABLE payments
    ADD CONSTRAINT fk_payments_account_id
    FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE SET NULL;

-- ── Key operations (outbox) ───────────────────────────────────────────────

CREATE TYPE key_operation_action AS ENUM (
    'create',   -- Создать ключ на панели
    'update',   -- Обновить ключ (продление срока)
    'delete',   -- Удалить ключ
    'enable',   -- Включить ключ
    'disable'   -- Выключить ключ
);

CREATE TYPE key_operation_status AS ENUM (
    'pending',     -- Ожидает обработки
    'processing',  -- В процессе обработки
    'completed',   -- Успешно выполнено
    'failed'       -- Ошибка (исчерпаны попытки)
);

CREATE TABLE IF NOT EXISTS key_operations (
    operation_id    SERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    subscription_id UUID   NOT NULL REFERENCES subscriptions (subscription_id) ON DELETE CASCADE,
    server_id       INTEGER NOT NULL REFERENCES servers (server_id) ON DELETE CASCADE,
    action          key_operation_action NOT NULL,
    days            INTEGER,
    status          key_operation_status NOT NULL DEFAULT 'pending',
    retry_count     INTEGER NOT NULL DEFAULT 0,
    max_retries     INTEGER NOT NULL DEFAULT 10,
    error_message   TEXT,
    -- scheduled_at позволяет реализовать backoff при повторных попытках
    scheduled_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at      TIMESTAMP WITH TIME ZONE,
    completed_at    TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_days_positive CHECK (days IS NULL OR days > 0),
    CONSTRAINT chk_retry_count_non_negative CHECK (retry_count >= 0),
    CONSTRAINT chk_max_retries_positive CHECK (max_retries > 0)
);

CREATE INDEX IF NOT EXISTS idx_key_operations_pending
    ON key_operations (scheduled_at)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_key_operations_subscription
    ON key_operations (subscription_id);
