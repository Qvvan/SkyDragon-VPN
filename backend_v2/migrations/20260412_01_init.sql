-- depends:

-- ── Subscriptions ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id SERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    service_id      INTEGER NULL,
    start_date      TIMESTAMP NULL,
    end_date        TIMESTAMP NULL,
    status          VARCHAR(64) NULL,
    reminder_sent   INTEGER NOT NULL DEFAULT 0,
    auto_renewal    BOOLEAN NOT NULL DEFAULT TRUE,
    card_details_id VARCHAR(255) NULL,
    account_id      BIGINT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_subscription
    ON subscriptions (user_id, subscription_id);

CREATE INDEX IF NOT EXISTS idx_subscriptions_account_id
    ON subscriptions (account_id)
    WHERE account_id IS NOT NULL;

-- ── Servers ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS servers (
    server_ip       VARCHAR(255) PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    "limit"         INTEGER NULL,
    hidden          INTEGER NOT NULL DEFAULT 0,
    available_ports VARCHAR(255) NULL,
    panel_port      INTEGER NULL,
    url_secret      VARCHAR(255) NULL,
    sub_port        INTEGER NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Services ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS services (
    service_id    SERIAL PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    duration_days INTEGER NOT NULL,
    price         INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_services_duration_days
    ON services (duration_days);

-- ── Payments ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS payments (
    id                SERIAL PRIMARY KEY,
    payment_id        VARCHAR(255) NOT NULL UNIQUE,
    user_id           BIGINT NOT NULL,
    recipient_user_id BIGINT NULL,
    service_id        INTEGER NULL,
    status            VARCHAR(64) NOT NULL DEFAULT 'pending',
    payment_type      VARCHAR(64) NULL DEFAULT 'myself',
    receipt_link      VARCHAR(1024) NULL,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ── Accounts ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS accounts (
    id            BIGSERIAL PRIMARY KEY,
    login         VARCHAR(64) NOT NULL,
    password_hash TEXT NOT NULL,
    first_name    VARCHAR(128) NOT NULL DEFAULT '',
    last_name     VARCHAR(128) NOT NULL DEFAULT '',
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_login
    ON accounts (login);

-- ── Account ↔ Telegram links ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS account_telegram_links (
    telegram_user_id BIGINT PRIMARY KEY,
    account_id       BIGINT NOT NULL REFERENCES accounts (id) ON DELETE CASCADE,
    linked_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_account_telegram_links_one_tg_per_account UNIQUE (account_id)
);

CREATE INDEX IF NOT EXISTS idx_account_telegram_links_account_id
    ON account_telegram_links (account_id);

-- ── Subscription provision tasks (outbox) ────────────────────────────────

CREATE TABLE IF NOT EXISTS subscription_provision_tasks (
    id              BIGSERIAL PRIMARY KEY,
    subscription_id INTEGER NOT NULL REFERENCES subscriptions (subscription_id) ON DELETE CASCADE,
    user_id         BIGINT NOT NULL,
    server_ip       VARCHAR(255) NOT NULL,
    action          VARCHAR(32) NOT NULL CHECK (action IN ('create', 'update', 'delete')),
    status          VARCHAR(32) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'processing', 'done', 'failed')),
    attempts        INTEGER NOT NULL DEFAULT 0,
    max_attempts    INTEGER NOT NULL DEFAULT 5,
    last_error      TEXT NULL,
    expire_at       TIMESTAMP NULL,
    scheduled_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    done_at         TIMESTAMP NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_provision_tasks_pending
    ON subscription_provision_tasks (scheduled_at)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_provision_tasks_subscription
    ON subscription_provision_tasks (subscription_id);
