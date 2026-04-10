DROP INDEX IF EXISTS idx_subscriptions_account_id;
ALTER TABLE subscriptions DROP COLUMN IF EXISTS account_id;

DROP TABLE IF EXISTS telegram_link_codes;
DROP TABLE IF EXISTS account_telegram_links;
DROP INDEX IF EXISTS idx_accounts_phone;
DROP INDEX IF EXISTS idx_accounts_email_lower;
DROP TABLE IF EXISTS accounts;
