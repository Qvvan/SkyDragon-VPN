-- depends:

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    service_id INTEGER NULL,
    start_date TIMESTAMP NULL,
    end_date TIMESTAMP NULL,
    status VARCHAR(64) NULL,
    reminder_sent INTEGER NOT NULL DEFAULT 0,
    auto_renewal BOOLEAN NOT NULL DEFAULT TRUE,
    card_details_id VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS servers (
    server_ip VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    "limit" INTEGER NULL,
    hidden INTEGER NOT NULL DEFAULT 0,
    available_ports VARCHAR(255) NULL,
    panel_port INTEGER NULL,
    url_secret VARCHAR(255) NULL,
    sub_port INTEGER NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS services (
    service_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    duration_days INTEGER NOT NULL,
    price INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    payment_id VARCHAR(255) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL,
    recipient_user_id BIGINT NULL,
    service_id INTEGER NULL,
    status VARCHAR(64) NOT NULL DEFAULT 'pending',
    payment_type VARCHAR(64) NULL DEFAULT 'myself',
    receipt_link VARCHAR(1024) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_subscription
    ON subscriptions(user_id, subscription_id);

CREATE INDEX IF NOT EXISTS idx_services_duration_days
    ON services(duration_days);
