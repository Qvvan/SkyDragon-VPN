-- depends: 20260409_01_baseline_subscriptions

CREATE TABLE IF NOT EXISTS accounts (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(320) NULL,
    phone VARCHAR(32) NULL,
    password_hash TEXT NOT NULL,
    first_name VARCHAR(128) NOT NULL DEFAULT '',
    last_name VARCHAR(128) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_email_lower
    ON accounts (LOWER(email))
    WHERE email IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_phone
    ON accounts (phone)
    WHERE phone IS NOT NULL;

CREATE TABLE IF NOT EXISTS account_telegram_links (
    telegram_user_id BIGINT PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES accounts (id) ON DELETE CASCADE,
    linked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_account_telegram_links_one_tg_per_account UNIQUE (account_id)
);

CREATE INDEX IF NOT EXISTS idx_account_telegram_links_account_id
    ON account_telegram_links (account_id);

CREATE TABLE IF NOT EXISTS telegram_link_codes (
    code VARCHAR(16) PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES accounts (id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_account_id
    ON telegram_link_codes (account_id);

ALTER TABLE subscriptions
    ADD COLUMN IF NOT EXISTS account_id BIGINT NULL REFERENCES accounts (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_subscriptions_account_id
    ON subscriptions (account_id)
    WHERE account_id IS NOT NULL;
